import pygame
import sys
import time
from func_timeout import func_timeout, FunctionTimedOut

from boardclasses import *


# Such numbers so as to simplify the debugging process
MAX_TYPE = 3
MIN_TYPE = 4
ITERATIVE_DEEPENING = True


def generate_conversion_dictionaries():
	letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S']
	numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19']

	havannah_notation_list = []
	for i in list(range(10, 20)):
		number = numbers[i - 10]
		for j in range(0, i):
			havannah_notation_string = number + ' ' + letters[j]
			havannah_notation_list.append(havannah_notation_string)

	for i in list(range(10, 19)):
		number = numbers[i]
		for j in range(28 - i):
			havannah_notation_string = number + ' ' + letters[j + i - 9]
			havannah_notation_list.append(havannah_notation_string)

	my_notation_list = []

	column_ranges = [(5,14), (4,14), (4,15), (3,15), (3,16), (2,16), (2,17), (1,17), (1,18), (0,18), 
					 (1,18), (1,17), (2,17), (2,16), (3,16), (3,15), (4,15), (4,14), (5,14)]

	for i in range(0,19):
		for j in range(column_ranges[i][0], column_ranges[i][1] + 1):
			my_notation_string = str(i) + ' ' + str(j)
			my_notation_list.append(my_notation_string)

	havannah_to_my_notation_dict = dict(zip(havannah_notation_list, my_notation_list))
	my_notation_to_havannah_dict = dict(zip(my_notation_list, havannah_notation_list))

	return havannah_to_my_notation_dict, my_notation_to_havannah_dict


def get_haxagon_points(hex_x, hex_y):
	p1 = (hex_x, hex_y - HEX_SIDE)
	p2 = (hex_x + HEX_SIDE * math.sqrt(3) / 2, hex_y - HEX_SIDE / 2)
	p3 = (hex_x + HEX_SIDE * math.sqrt(3) / 2, hex_y + HEX_SIDE / 2)
	p4 = (hex_x, hex_y + HEX_SIDE)
	p5 = (hex_x - HEX_SIDE * math.sqrt(3) / 2, hex_y + HEX_SIDE / 2)
	p6 = (hex_x - HEX_SIDE * math.sqrt(3) / 2, hex_y - HEX_SIDE / 2)

	return(p1, p2, p3, p4, p5, p6)


def draw_grid(valid_hexagons, color, surface):
	for hex in valid_hexagons:
		pygame.draw.polygon(surface, color, get_haxagon_points(hex.x, hex.y) , 1)


def draw_pawns(pawn_hexagons, color, surface):
	for hex in pawn_hexagons:
		pygame.draw.circle(surface, color, (int(hex.x), int(hex.y)), CIRCLE_RADIUS)


def perform_iterative_deepening(boardState):
	THRESHOLD = 3
	MAX_DEPTH = 20
	time_out = False
	depth = 1

	infinity = float('inf')
	minus_infinity = float('-inf')

	valid_moves = boardState.get_valid_moves()
	potential_states = [boardState.make_move(vm.row, vm.column)[1] for vm in valid_moves]
	potential_states.sort(key=lambda state: state.evaluate_state())
	potential_states.reverse()

	while True:
		best_score = float('-inf')
		best_next_state = None	

		time_passed = 0

		for potential_state in potential_states:
			try:
				start_time=time.time()
				#score = func_timeout(THRESHOLD, alpha_beta, (potential_state, depth, minus_infinity, infinity, MAX_TYPE))
				score = func_timeout(THRESHOLD, pvs, (potential_state, depth, minus_infinity, infinity))
				end_time=time.time()
				current_time_passed = end_time - start_time
				THRESHOLD -= current_time_passed
			except FunctionTimedOut:
				print ("TIME OUT!")
				time_out = True
				break			

			if score > best_score:
				best_score = score
				best_next_state = potential_state

			time_passed = max(current_time_passed, time_passed)

		if time_out:
			break

		print("Max time for depth {}: {}s".format(depth, time_passed))

		__, boardStateHolder = boardState.make_move(best_next_state.last_move_hex.row, best_next_state.last_move_hex.column)

		depth += 2
		if depth > MAX_DEPTH:
			break

	return boardStateHolder


def pvs(board_state, depth, alpha, beta):
	if (board_state.terminal_node or depth == 0):
		return board_state.evaluate_state()

	valid_moves = board_state.get_valid_moves()
	children = [board_state.make_move(vm.row, vm.column)[1] for vm in valid_moves]
	children.sort(key=lambda state: state.evaluate_state())
	children.reverse()

	for i in range(0, len(children)):
		if i == 0:
			score = -pvs(children[i], depth - 1, -beta, -alpha)
			return score
		else:
			score = -pvs(children[i], depth - 1, -alpha - 1, -alpha)
			if (alpha < score and score < beta):
				score = -pvs(children[i], depth - 1, -beta, -score)

		alpha = max(alpha, score)
		if alpha >= beta:
			break

	return alpha


def alpha_beta_negamax(board_state, depth, alpha, beta):
	if (board_state.terminal_node or depth == 0):
		return -board_state.evaluate_state()

	valid_moves = board_state.get_valid_moves()
	children = [board_state.make_move(vm.row, vm.column)[1] for vm in valid_moves]

	children.sort(key=lambda state: state.evaluate_state())
	children.reverse()

	score = float('-inf')

	for child in children:
		value = -alpha_beta_negamax(child, depth - 1, -beta, -alpha)

		if value > score:
			score = value

		if score > alpha:
			alpha = score

		if score >= beta:
			break

	return score


def alpha_beta(board_state, depth, alpha, beta, player_type):
	if (board_state.terminal_node or depth == 0):
		return board_state.evaluate_state()

	valid_moves = board_state.get_valid_moves()
	children = [board_state.make_move(vm.row, vm.column)[1] for vm in valid_moves]


	children.sort(key=lambda state: state.evaluate_state())

	if player_type == MAX_TYPE:
		children.reverse()
		score = float('-inf')
		for child in children:
			value = alpha_beta(child, depth - 1, alpha, beta, MIN_TYPE)
			score = max(score, value)
			alpha = max(alpha, score)
			if alpha >= beta:
				break # beta cut-off
		return score
	else: # MIN player
		score = float('inf')
		for child in children:
			value = alpha_beta(child, depth - 1, alpha, beta, MAX_TYPE)
			score = min(score, value)
			beta = min(beta, score)
			if alpha >= beta:
				break # alpha cut-off
		return score



def minimax(board_state, depth, player_type):
	if (board_state.terminal_node or depth == 0):
		return board_state.evaluate_state()

	valid_moves = board_state.get_valid_moves()
	children = [board_state.make_move(vm.row, vm.column)[1] for vm in valid_moves]

	if player_type == MAX_TYPE:
		score = float('-inf')
		for child in children:
			value = minimax(child, depth - 1, MIN_TYPE)
			score = max(score, value)
	else:
		score = float('inf')
		for child in children:
			value = minimax(child, depth - 1, MAX_TYPE)
			score = min(score, value)

	return score

# # # # #

window_size = (750, 650)

pygame.init()

surface = pygame.display.set_mode(window_size)

bg_color = pygame.color.Color(240, 230, 140)
black_color = pygame.color.Color('Black')
white_color = pygame.color.Color('White')

polygon_color = pygame.color.Color('Blue')
green_color = pygame.color.Color('Green')
red_color = pygame.color.Color('Red')
magenta_color = pygame.color.Color(255, 0, 255)


havannah_to_my_notation_dict, my_notation_to_havannah_dict = generate_conversion_dictionaries()

input_row = -1
input_column = -1

first_iteration = True
game_finished = False

# For moves and players (black/white) distinction
game_round = 1

# For the player choice
# Alternate it as follows: 0 -> computer (AI) goes first, 1 -> human player goes first. Black player always goes first (starting in the centre).
round_counter = 1

player1_hexagons = []
player2_hexagons = []
boardState = BoardState(player1_hexagons, player2_hexagons, None, game_round, PLAYER_1)

while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()

	# First iteration is only to draw everything (grid and the valid move)
	if first_iteration: 
		first_iteration = False	
	elif game_finished:
		pass
	else:
		if round_counter % 2 != 0: # human player's turn
			input_string = input("Enter hex data using Havannah notation: (e.g. '1 A')\n")
			input_string = input_string.upper()
			try:
				converted_string = havannah_to_my_notation_dict[input_string]
				(input_row_string, input_column_string) = converted_string.split(" ")
				input_row = int(input_row_string)
				input_column = int(input_column_string)
			except (KeyError):
				print("Incorrect input. Try again.")
				continue
			
			print("Move to be made by human: ({},{})".format(input_row, input_column))

			was_move_made, boardStateHolder = boardState.make_move(input_row, input_column) 
			if was_move_made:
				round_counter += 1
				boardState = boardStateHolder
				print("MOVE MADE")
				print(">>> ({},{}) <<<".format(boardState.last_move_hex.row, boardState.last_move_hex.column))
				
				win = boardState.check_if_win()
		
				if win:
					bg_color = pygame.color.Color('Green')
					game_finished = True

					if boardState.current_player == PLAYER_1: #current player of the new state, so the last move, which caused the winning state belongs to the opposite player
						print("\n=== PLAYER 2 (WHTIE) WON ===\n")
					else:
						print("\n=== PLAYER 1 (BLACK) WON ===\n")

					print("The game has stopped")
		
		elif ITERATIVE_DEEPENING: #computer's turn but with iterative deepening
			boardStateHolder = perform_iterative_deepening(boardState)
			boardState = boardStateHolder

			round_counter += 1
				
			print(">>> [AI] MOVE MADE <<<")

			made_move_row = str(boardState.last_move_hex.row)
			made_move_column = str(boardState.last_move_hex.column)

			move_havannah_string = my_notation_to_havannah_dict[made_move_row + ' ' + made_move_column]
			print(">>> {} <<<".format(move_havannah_string))

			win = boardState.check_if_win()
	
			if win:
				bg_color = pygame.color.Color('Red')
				game_finished = True

				if boardState.current_player == PLAYER_1: #current player of the new state, so the last move, which caused the winning state belongs to the opposite player
					print("\n=== PLAYER 2 (WHTIE) WON ===\n")
				else:
					print("\n=== PLAYER 1 (BLACK) WON ===\n")

				print("The game has stopped")
		
		else: # computer's turn (no iterative deepening)
			valid_moves = boardState.get_valid_moves()

			best_score = float('-inf')
			best_next_state = None

			infinity = float('inf')
			minus_infinity = float('-inf')
			
			potential_states = [boardState.make_move(vm.row, vm.column)[1] for vm in valid_moves]
			potential_states.sort(key=lambda state: state.evaluate_state())
			potential_states.reverse()

			start_time_measurement = time.time()

			for potential_state in potential_states:
				#score = minimax(potential_state, 3, MAX_TYPE) 
				#print("Score after minimax: {}".format(score))
				
				#score = alpha_beta_negamax(potential_state, 5, minus_infinity, infinity)
				#score = math.fabs(score)
				#print("Score after alpha beta negamax: {}".format(score))
				
				#score = alpha_beta(potential_state, 5, minus_infinity, infinity, MAX_TYPE)
				#print("Score after alpha beta (normal): {}".format(score))

				score = pvs(potential_state, 5, minus_infinity, infinity)
				score = math.fabs(score)
				print("Score after pvs: {}".format(score))

				if score > best_score:
					best_score = score
					best_next_state = potential_state
			
			end_time_measurement = time.time()

			print("+++ Time elapsed for making the AI move: {}".format(end_time_measurement - start_time_measurement))

			__, boardStateHolder = boardState.make_move(best_next_state.last_move_hex.row, best_next_state.last_move_hex.column)
			boardState = boardStateHolder
			
			round_counter += 1
		
			print(">>> [AI] MOVE MADE <<<")

			made_move_row = str(boardState.last_move_hex.row)
			made_move_column = str(boardState.last_move_hex.column)

			move_havannah_string = my_notation_to_havannah_dict[made_move_row + ' ' + made_move_column]
			print(">>> {} <<<".format(move_havannah_string))

			win = boardState.check_if_win()
	
			if win:
				bg_color = pygame.color.Color('Red')
				game_finished = True

				if boardState.current_player == PLAYER_1: #current player of the new state, so the last move, which caused the winning state belongs to the opposite player
					print("\n=== PLAYER 2 (WHTIE) WON ===\n")
				else:
					print("\n=== PLAYER 1 (BLACK) WON ===\n")

				print("The game has stopped")
		
		
	# Draw everything
	surface.fill(bg_color)

	draw_grid(BoardState.valid_hexagons, polygon_color, surface)

	draw_pawns(boardState.player1_hexagons, black_color, surface)
	draw_pawns(boardState.player2_hexagons, white_color, surface)

	draw_pawns(boardState.valid_moves, magenta_color, surface)

	pygame.display.flip()
