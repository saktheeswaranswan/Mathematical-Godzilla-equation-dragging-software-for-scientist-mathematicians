import pygame
import sympy as sp

pygame.init()

# Screen setup
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SymPy Drag & Solve")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)     # For objects on LHS
GREEN = (0, 255, 0)    # For objects on RHS
GRAY = (200, 200, 200)

# Fonts
font = pygame.font.Font(None, 36)

# Define symbol and initial expression.
x = sp.Symbol('x')
expr = sp.sympify("2*x + 3")  # Example expression: 2*x + 3

# Our equation is built as: (sum of contributions) = 0.
solution = None
history = []

# We'll represent each draggable item as a dictionary.
# Each object has an "id", an optional "group" (to link parts of the same term),
# a "part" (which can be "coeff", "var", or "single"), a display "text",
# its Sympy "expr", its current screen "pos", and its "location" (either "lhs" or "rhs").
draggable_objects = []
object_id = 0

def add_draggable_object(group, part, text, expr_value, pos, location="lhs"):
    global object_id
    draggable_objects.append({
        "id": object_id,
        "group": group,     # None if it's a standalone term; otherwise, a group id.
        "part": part,       # "coeff" for coefficient, "var" for variable part, "single" otherwise.
        "text": text,
        "expr": expr_value, # A Sympy object (number, symbol, or expression).
        "pos": pos,
        "location": location
    })
    object_id += 1

# Parse the expression into terms.
# For each term, if it involves x and is a multiplication, we separate the coefficient.
terms_list = expr.as_ordered_terms()
group_id = 0
for term in terms_list:
    # If term has x and is a multiplication, try to split it.
    if term.has(x) and term.is_Mul:
        coeff, factors = term.as_coeff_mul(x)
        # If coefficient is something other than 1 or -1, split into two parts.
        if coeff != 1 and coeff != -1:
            add_draggable_object(group=group_id, part="coeff", text=str(coeff),
                                   expr_value=sp.Integer(coeff), pos=(150 + group_id*150, 200))
            # Reconstruct the variable part (multiplication of the remaining factors).
            var_part = sp.Mul(*factors)
            add_draggable_object(group=group_id, part="var", text=str(var_part),
                                   expr_value=var_part, pos=(150 + group_id*150 + 60, 200))
            group_id += 1
        else:
            # If coefficient is 1 or -1, treat the term as a single draggable object.
            add_draggable_object(group=None, part="single", text=str(term),
                                   expr_value=term, pos=(150 + group_id*150, 200))
            group_id += 1
    else:
        # Constant or term without x is a single draggable object.
        add_draggable_object(group=None, part="single", text=str(term),
                               expr_value=term, pos=(150 + group_id*150, 200))
        group_id += 1

dragging = False
selected_object = None

def update_equation():
    """
    Rebuilds the equation based on the current positions/locations of the draggable objects.
    For compound (grouped) terms, if the coefficient and variable parts are on the same side,
    the effective term is coefficient * variable.
    If they are split (on opposite sides), it applies the inverse: the effective term becomes variable divided by coefficient.
    Each object’s location determines its sign: terms on the LHS contribute positively, those on the RHS negatively.
    """
    global history
    lhs_expr = 0
    processed_groups = set()
    # Process grouped (compound) terms.
    for obj in draggable_objects:
        if obj["group"] is not None:
            group = obj["group"]
            if group in processed_groups:
                continue
            group_objs = [o for o in draggable_objects if o["group"] == group]
            if len(group_objs) != 2:
                continue
            coeff_obj = next(o for o in group_objs if o["part"] == "coeff")
            var_obj = next(o for o in group_objs if o["part"] == "var")
            # If both parts are on the same side, effective factor is the coefficient;
            # otherwise, moving the coefficient to the opposite side implies dividing by it.
            if coeff_obj["location"] == var_obj["location"]:
                effective_factor = coeff_obj["expr"]
            else:
                effective_factor = 1 / coeff_obj["expr"]
            effective_term = effective_factor * var_obj["expr"]
            # Use the location of the variable part to determine sign.
            sign = 1 if var_obj["location"] == "lhs" else -1
            lhs_expr += sign * effective_term
            processed_groups.add(group)
    # Process single objects.
    for obj in draggable_objects:
        if obj["group"] is None:
            sign = 1 if obj["location"] == "lhs" else -1
            lhs_expr += sign * obj["expr"]
    eq = sp.Eq(lhs_expr, 0)
    history.append(f"Updated equation: {eq}")
    return eq

def solve_equation(eq):
    global solution, history
    solution = sp.solve(eq, x)
    history.append(f"Solved equation: {eq} -> x = {solution}")

def draw_text(text, pos, color=BLACK):
    render = font.render(text, True, color)
    screen.blit(render, pos)

running = True
while running:
    screen.fill(WHITE)
    # Draw LHS and RHS boxes.
    pygame.draw.rect(screen, GRAY, (50, 150, 400, 200))   # LHS box
    pygame.draw.rect(screen, GRAY, (550, 150, 400, 200))    # RHS box
    draw_text("LHS", (200, 120))
    draw_text("RHS", (700, 120))
    draw_text("=", (WIDTH//2 - 20, 230))
    
    # Draw all draggable objects.
    for obj in draggable_objects:
        col = BLUE if obj["location"] == "lhs" else GREEN
        draw_text(obj["text"], obj["pos"], col)
    
    # Display solution (if available).
    if solution is not None:
        draw_text(f"Solution: x = {solution}", (20, 60), BLUE)
    
    # Display recent history.
    y_offset = 400
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
                # Simple hit detection.
                if ox - 50 < mx < ox + 100 and oy - 20 < my < oy + 40:
                    dragging = True
                    selected_object = obj
                    break
        
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
            if selected_object:
                # When dropped, assign location based on horizontal position.
                ox, _ = selected_object["pos"]
                if ox < WIDTH // 2:
                    selected_object["location"] = "lhs"
                else:
                    selected_object["location"] = "rhs"
                eq = update_equation()
            selected_object = None
        
        elif event.type == pygame.MOUSEMOTION and dragging:
            selected_object["pos"] = event.pos
        
        elif event.type == pygame.KEYDOWN:
            # Press S to update the equation and solve for x.
            if event.key == pygame.K_s:
                eq = update_equation()
                solve_equation(eq)
    
    pygame.display.flip()

pygame.quit()

