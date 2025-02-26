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
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)

# Fonts
font = pygame.font.Font(None, 36)

# Define the symbol and initial expression.
x = sp.Symbol('x')
# Example: 2*x + 3 - 5. You can change this to any expression.
expr = sp.sympify("2*x + 3 - 5")

# Break the expression into its ordered terms.
terms_list = expr.as_ordered_terms()

# Create a dictionary for draggable terms.
# Each term is stored with its sympy expression, its string label,
# its current screen position, and its "location": either 'lhs' or 'rhs'.
draggable_terms = {}
for i, term in enumerate(terms_list):
    label = str(term)
    draggable_terms[label] = {
        "expr": term,
        "pos": (200 + i * 150, 200),
        "location": "lhs"  # Initially, every term is on the LHS.
    }

solution = None
history = []

dragging = False
selected_key = None

def update_equation():
    """
    Rebuilds the equation using the current positions:
      - Terms in the left box (location 'lhs') are added.
      - Terms in the right box (location 'rhs') are subtracted.
    """
    lhs_expr = 0
    rhs_expr = 0
    for key, data in draggable_terms.items():
        if data["location"] == "lhs":
            lhs_expr += data["expr"]
        else:
            # For terms on the RHS, we subtract them from the LHS.
            lhs_expr -= data["expr"]
    # Build the equation as lhs_expr = 0.
    eq = sp.Eq(lhs_expr, 0)
    history.append(f"Updated equation: {eq}")
    return eq

def solve_expression(eq):
    global solution
    solution = sp.solve(eq, x)
    history.append(f"Solving for x: {eq} -> x = {solution}")

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
    draw_text("=", (WIDTH // 2 - 20, 230))
    
    # Draw all draggable terms.
    for key, data in draggable_terms.items():
        col = BLUE if data["location"] == "lhs" else GREEN
        draw_text(key, data["pos"], col)
    
    # Display solution (if available)
    if solution is not None:
        draw_text(f"Solution: x = {solution}", (20, 60), BLUE)
    
    # Display recent history (last 5 steps)
    y_offset = 400
    for hist in history[-5:]:
        draw_text(hist, (20, y_offset), GREEN)
        y_offset += 30

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Check if mouse is over any term.
            for key, data in draggable_terms.items():
                tx, ty = data["pos"]
                if tx - 50 < mx < tx + 100 and ty - 20 < my < ty + 40:
                    dragging = True
                    selected_key = key
                    break

        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
            if selected_key:
                # Update location based on where the term is dropped.
                tx, ty = draggable_terms[selected_key]["pos"]
                if tx < WIDTH // 2:
                    draggable_terms[selected_key]["location"] = "lhs"
                else:
                    draggable_terms[selected_key]["location"] = "rhs"
                # After moving, update the equation.
                eq = update_equation()
            selected_key = None

        elif event.type == pygame.MOUSEMOTION and dragging:
            # Move the selected term with the mouse.
            draggable_terms[selected_key]["pos"] = event.pos

        elif event.type == pygame.KEYDOWN:
            # Press S to solve the current equation.
            if event.key == pygame.K_s:
                eq = update_equation()
                solve_expression(eq)

    pygame.display.flip()

pygame.quit()

