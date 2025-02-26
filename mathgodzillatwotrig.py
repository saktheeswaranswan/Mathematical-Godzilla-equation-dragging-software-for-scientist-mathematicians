import pygame
import sympy as sp

pygame.init()

# Screen setup
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Advanced SymPy Drag & Solve")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)     # For objects on LHS
GREEN = (0, 255, 0)    # For objects on RHS
GRAY = (200, 200, 200)

# Fonts
font = pygame.font.Font(None, 28)

# Define the symbol and a more complex expression.
x = sp.Symbol('x')
# Note: Removed the "sp." prefixes so that sympy can parse the functions correctly.
expr = sp.sympify("2*sin(x) + 3*cos(x) + exp(x) + tanh(x)")

solution = None
history = []

# Each draggable item is represented as a dictionary.
# It stores: id, group (for compound terms), part (e.g. 'coeff', 'func', 'var', or 'single'),
# text (for display), its sympy expression, current position, location ('lhs' or 'rhs'),
# and an 'inverted' flag to indicate if a function has been moved.
draggable_objects = []
object_id = 0

# Mapping for functions to their inverses (if available).
inverse_mapping = {
    sp.sin: sp.asin,
    sp.cos: sp.acos,
    sp.tan: sp.atan,
    sp.exp: sp.log,
    sp.tanh: sp.atanh,
}

def add_draggable_object(group, part, text, expr_value, pos, location="lhs"):
    global object_id
    draggable_objects.append({
        "id": object_id,
        "group": group,       # If not None, indicates this object is linked with others.
        "part": part,         # "coeff", "func", "var", or "single".
        "text": text,
        "expr": expr_value,   # A sympy object (number, symbol, function, etc.)
        "pos": pos,
        "location": location, # "lhs" or "rhs"
        "inverted": False     # For function objects: if moved to the opposite side.
    })
    object_id += 1

# Parse the expression into draggable objects.
# We break the expression by addition.
terms_list = expr.as_ordered_terms()
group_id = 0
for term in terms_list:
    # For a multiplication involving x, try to split coefficient from the rest.
    if term.has(x) and term.is_Mul:
        coeff, rest = term.as_coeff_Mul()
        if coeff not in [1, -1]:
            add_draggable_object(group=group_id, part="coeff", text=str(coeff),
                                   expr_value=sp.Integer(coeff), pos=(150 + group_id*180, 200))
            add_draggable_object(group=group_id, part="var", text=str(rest),
                                   expr_value=rest, pos=(150 + group_id*180 + 60, 200))
            group_id += 1
        else:
            # If coefficient is ±1, check if it's a function (like sin, cos, etc.).
            if isinstance(rest, sp.Function):
                add_draggable_object(group=group_id, part="func", text=str(rest),
                                       expr_value=rest, pos=(150 + group_id*180, 200))
                group_id += 1
            else:
                add_draggable_object(group=None, part="single", text=str(term),
                                       expr_value=term, pos=(150 + group_id*180, 200))
                group_id += 1
    elif term.func in [sp.sin, sp.cos, sp.tan, sp.exp, sp.tanh]:
        # Directly treat these as function terms.
        add_draggable_object(group=group_id, part="func", text=str(term),
                               expr_value=term, pos=(150 + group_id*180, 200))
        group_id += 1
    else:
        # For constants or other standalone terms.
        add_draggable_object(group=None, part="single", text=str(term),
                               expr_value=term, pos=(150 + group_id*180, 200))
        group_id += 1

dragging = False
selected_object = None

def process_object(obj):
    """
    Returns the effective sympy expression for an object.
    If the object is a function and has been inverted (moved across the equation),
    apply the inverse function from our mapping.
    """
    effective_expr = obj["expr"]
    if obj["inverted"] and obj["part"] == "func":
        func = effective_expr.func
        if func in inverse_mapping:
            arg = effective_expr.args[0]
            effective_expr = inverse_mapping[func](arg)
    return effective_expr

def update_equation():
    """
    Rebuilds the equation based on the current positions/locations of the draggable objects.
    For compound terms (grouped objects), if the coefficient and the rest are on the same side,
    then the effective term is (coefficient * rest). If they are on opposite sides, then the move
    implies dividing by the coefficient (i.e. multiplying by its inverse).
    For single objects, a term on the LHS is added and on the RHS subtracted.
    """
    global history
    lhs_expr = 0
    processed_groups = set()
    for obj in draggable_objects:
        if obj["group"] is not None:
            group = obj["group"]
            if group in processed_groups:
                continue
            group_objs = [o for o in draggable_objects if o["group"] == group]
            if len(group_objs) == 2:
                coeff_obj = next((o for o in group_objs if o["part"] == "coeff"), None)
                other_obj = next((o for o in group_objs if o["part"] != "coeff"), None)
                if coeff_obj and other_obj:
                    if coeff_obj["location"] == other_obj["location"]:
                        effective = coeff_obj["expr"] * other_obj["expr"]
                    else:
                        effective = other_obj["expr"] / coeff_obj["expr"]
                    sign = 1 if other_obj["location"] == "lhs" else -1
                    lhs_expr += sign * effective
            else:
                # Incomplete group: process individually.
                for o in group_objs:
                    sign = 1 if o["location"] == "lhs" else -1
                    lhs_expr += sign * process_object(o)
            processed_groups.add(group)
        else:
            sign = 1 if obj["location"] == "lhs" else -1
            lhs_expr += sign * process_object(obj)
    eq = sp.Eq(lhs_expr, 0)
    history.append(f"Updated eq: {eq}")
    return eq

def solve_eq(eq):
    global solution, history
    try:
        solution = sp.solve(eq, x)
        history.append(f"Solved eq: {eq} -> x = {solution}")
    except Exception as e:
        history.append(f"Error solving eq: {e}")

def integrate_eq(eq):
    global solution, history
    try:
        solution = sp.integrate(eq.lhs, x)
        history.append(f"Integrated eq lhs: {eq.lhs} dx -> {solution}")
    except Exception as e:
        history.append(f"Error integrating eq: {e}")

def differentiate_eq(eq):
    global solution, history
    try:
        solution = sp.diff(eq.lhs, x)
        history.append(f"Differentiated eq lhs: {eq.lhs} -> {solution}")
    except Exception as e:
        history.append(f"Error differentiating eq: {e}")

def draw_text(text, pos, color=BLACK):
    render = font.render(text, True, color)
    screen.blit(render, pos)

running = True
while running:
    screen.fill(WHITE)
    # Draw boxes for LHS and RHS.
    pygame.draw.rect(screen, GRAY, (50, 150, 400, 200))   # LHS box
    pygame.draw.rect(screen, GRAY, (750, 150, 400, 200))   # RHS box
    draw_text("LHS", (200, 120))
    draw_text("RHS", (900, 120))
    draw_text("=", (WIDTH//2 - 20, 230))
    
    # Draw draggable objects.
    for obj in draggable_objects:
        col = BLUE if obj["location"] == "lhs" else GREEN
        draw_text(obj["text"], obj["pos"], col)
    
    # Display solution.
    if solution is not None:
        draw_text(f"Solution: x = {solution}", (20, 60), BLUE)
    
    # Display recent history.
    y_offset = 500
    for hist in history[-5:]:
        draw_text(hist, (20, y_offset), GREEN)
        y_offset += 30
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            for obj in draggable_objects:
                ox, oy = obj["pos"]
                if ox - 50 < mx < ox + 100 and oy - 20 < my < oy + 40:
                    dragging = True
                    selected_object = obj
                    break
        
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
            if selected_object:
                ox, _ = selected_object["pos"]
                # Set location based on where the object is dropped.
                if ox < WIDTH//2:
                    selected_object["location"] = "lhs"
                else:
                    selected_object["location"] = "rhs"
                # For function objects, mark as inverted if moved to RHS.
                if selected_object["part"] == "func":
                    selected_object["inverted"] = (selected_object["location"] == "rhs")
                eq = update_equation()
            selected_object = None
        
        elif event.type == pygame.MOUSEMOTION and dragging:
            selected_object["pos"] = event.pos
        
        elif event.type == pygame.KEYDOWN:
            # S to solve, I to integrate, D to differentiate.
            if event.key == pygame.K_s:
                eq = update_equation()
                solve_eq(eq)
            elif event.key == pygame.K_i:
                eq = update_equation()
                integrate_eq(eq)
            elif event.key == pygame.K_d:
                eq = update_equation()
                differentiate_eq(eq)
    
    pygame.display.flip()

pygame.quit()

