import math


CENTRAL_HEXAGON_ROW = 9
CENTRAL_HEXAGON_COLUMN = 9
HEX_SIDE = 20
CIRCLE_RADIUS = 10

PLAYER_1 = 1
PLAYER_2 = 2

DIRECTION_LEFT = 1
DIRECTION_RIGHT = 2
DIRECTION_UPPER_LEFT = 3
DIRECTION_UPPER_RIGHT = 4
DIRECTION_BOTTOM_LEFT = 5
DIRECTION_BOTTOM_RIGHT = 6


class Hexagon:
	def __init__(self, row, column, x, y):
		self.row = row
		self.column = column
		self.x = x # for drawing on the board
		self.y = y # as above

	def __str__(self):
		return "{}\t{}\t{}\t{}".format(self.row, self.column, self.x, self.y)


def create_all_hexagons():
	start_x = 50
	start_y = 50

	all_hexagons = []

	for row in range(0, 19, 2):
		for column in range(19):
			all_hexagons.append(Hexagon(row, column, start_x + column * HEX_SIDE * math.sqrt(3), start_y + row * 3 / 2 * HEX_SIDE))

	offset = HEX_SIDE * math.sqrt(3) / 2

	for row in range(1, 19, 2):
		for column in range(19):
			all_hexagons.append(Hexagon(row, column, start_x + offset + column * HEX_SIDE * math.sqrt(3), start_y + row * 3 / 2 * HEX_SIDE))

	return all_hexagons


def get_valid_hexagons():
	all_hexagons = create_all_hexagons()
	valid_column_ranges_per_row = [(5,14), (4,14), (4,15), (3,15), (3,16), (2,16), (2,17), (1,17), (1,18), (0,18), 
								   (1,18), (1,17), (2,17), (2,16), (3,16), (3,15), (4,15), (4,14), (5,14)]
	valid_hexagons = []
	for hex in all_hexagons:
		hex_row = hex.row
		hex_column = hex.column
		if hex_column >= valid_column_ranges_per_row[hex_row][0] and \
		   hex_column <= valid_column_ranges_per_row[hex_row][1]:
			valid_hexagons.append(hex)	

	return valid_hexagons


class BoardState:
	valid_hexagons = get_valid_hexagons()

	def __init__(self, player1_hexagons, player2_hexagons, last_move_hex, game_round, current_player):
		self.player1_hexagons = player1_hexagons # created separately for each BoardState -> COPY of the list with extra element added
		self.player2_hexagons = player2_hexagons # [as above for p1]

		# Used to determine appropriate valid moves (especially with respect to the first and second round)
		self.game_round = game_round 

		# Necessarily called after p1 and p2 hexagon lists and game_round have been already initialised
		self.valid_moves = self.get_valid_moves() # created (generated) separately for each BoardState
		self.last_move_hex = last_move_hex
		
		self.current_player = current_player

		self.terminal_node = self.check_if_win()


	def get_hexagon_neighbours(self, hexagon):
		hex_r = hexagon.row
		hex_c = hexagon.column

		neighbours_coordinates = [(hex_r, hex_c - 1), (hex_r, hex_c + 1), (hex_r - 1, hex_c), (hex_r + 1, hex_c)]
		if hex_r % 2 == 0:
			neighbours_coordinates.extend([(hex_r - 1, hex_c - 1), (hex_r + 1, hex_c - 1)])
		else:
			neighbours_coordinates.extend([(hex_r - 1, hex_c + 1), (hex_r + 1, hex_c + 1)])

		neighbours = []
		for hex in BoardState.valid_hexagons:
			if (hex.row, hex.column) in neighbours_coordinates:
				neighbours.append(hex)

		return neighbours


	def get_valid_moves(self):
		if self.game_round == 1:
			valid_moves = [hex for hex in BoardState.valid_hexagons if hex.row == CENTRAL_HEXAGON_ROW and hex.column == CENTRAL_HEXAGON_COLUMN]
		elif self.game_round == 2:
			# player 1 always goes first, so all of his first move neighbours are desired at this state
			valid_moves = self.get_hexagon_neighbours(self.player1_hexagons[0])
		else:
			# Put all neigbours in one big list (with repetitions)
			all_neighbours = []
			for p1 in self.player1_hexagons:
				all_neighbours.extend(self.get_hexagon_neighbours(p1))
			for p2 in self.player2_hexagons:
				all_neighbours.extend(self.get_hexagon_neighbours(p2))

			# Remove Neighbours that are occupied by player moves
			all_neighbours = [n for n in all_neighbours if n not in self.player1_hexagons and n not in self.player2_hexagons]

			# Find valid moves as neighbours intersections
			valid_moves = [hex for hex in set(all_neighbours) if all_neighbours.count(hex) > 1]

		return valid_moves


	def make_move(self, input_row, input_column):
		for hex in BoardState.valid_hexagons:
			if(hex.row == input_row and hex.column == input_column):
				# Check whether the move is legal
				# * not overlapping
				if (hex in self.player1_hexagons or hex in self.player2_hexagons):
					print("Invalid move [overlapping]")
					return False, None

				# * legal according to the game rules
				if hex not in self.valid_moves:
					print("Invalid move [by rules, adjacency violation]")
					return False, None

				new_player1_hexagons = self.player1_hexagons.copy()
				new_player2_hexagons = self.player2_hexagons.copy()

				if len(self.player1_hexagons) <= len(self.player2_hexagons): # TO BE CHANGED (?)
					new_player1_hexagons.append(hex)
				else:
					new_player2_hexagons.append(hex)

				next_player = PLAYER_1 if self.current_player == PLAYER_2 else PLAYER_2

				return True, BoardState(new_player1_hexagons, new_player2_hexagons, hex, self.game_round + 1, next_player)

		print("Invalid move [outside the grid]")
		return False, None

	def evaluate_state(self):
		horizontal = self.check_line_horizontal()
		ascending = self.check_line_ascending()
		descending = self.check_line_descending()

		value = max(horizontal, ascending, descending)

		win_by_enclosing = self.check_if_enclosing()
		if win_by_enclosing:
			value += 5

		last_move_neighbours = self.get_hexagon_neighbours(self.last_move_hex)

		last_move_adjacent_to_the_same_player = False

		#last player was p2
		if self.current_player == PLAYER_1:
			for lmn in last_move_neighbours:
				if lmn in self.player2_hexagons:
					last_move_adjacent_to_the_same_player = True
		else:
			for lmn in last_move_neighbours:
				if lmn in self.player1_hexagons:
					last_move_adjacent_to_the_same_player = True

		if not last_move_adjacent_to_the_same_player:
			value -=1
		
		return value


	### WINNING CHECK FROM HERE ON ###

	def check_if_win(self):
		if self.check_if_win_line():
			return True

		if self.check_if_enclosing():
			return True

		return False


	def check_if_win_line(self):
		if self.last_move_hex is None:
			return False

		if self.check_line_horizontal() >= 5:
			return True

		if self.check_line_ascending() >= 5:
			return True

		if self.check_line_descending() >= 5:
			return True

		return False


	def check_line_horizontal(self):
		last_hex_row = self.last_move_hex.row
		last_hex_column = self.last_move_hex.column
		line_counter = 1

		line_left = [hex for hex in BoardState.valid_hexagons if hex.row == last_hex_row and hex.column < last_hex_column and hex.column >= last_hex_column - 4]
		line_left.sort(key=lambda x: x.column)
		line_left.reverse()

		line_right = [hex for hex in BoardState.valid_hexagons if hex.row == last_hex_row and hex.column > last_hex_column and hex.column <= last_hex_column + 4]
		line_right.sort(key=lambda x: x.column)

		return self.check_if_five_in_line(line_left, line_right)


	def check_line_ascending(self):
		last_hex_row = self.last_move_hex.row
		last_hex_column = self.last_move_hex.column

		line_left = []
		line_right = []
		#odd row number
		if last_hex_row % 2 != 0: 
			for hex in BoardState.valid_hexagons:
				if (
						hex.row == last_hex_row + 1 and hex.column == last_hex_column or
						hex.row == last_hex_row + 2 and hex.column == last_hex_column - 1 or
						hex.row == last_hex_row + 3 and hex.column == last_hex_column - 1 or
						hex.row == last_hex_row + 4 and hex.column == last_hex_column - 2
				  ):
					line_left.append(hex)
				elif (
						hex.row == last_hex_row - 1 and hex.column == last_hex_column + 1 or
						hex.row == last_hex_row - 2 and hex.column == last_hex_column + 1 or
						hex.row == last_hex_row - 3 and hex.column == last_hex_column + 2 or
						hex.row == last_hex_row - 4 and hex.column == last_hex_column + 2
					):
					line_right.append(hex)
		#even row number
		else: 
			for hex in BoardState.valid_hexagons:
				if (
						hex.row == last_hex_row + 1 and hex.column == last_hex_column - 1 or
						hex.row == last_hex_row + 2 and hex.column == last_hex_column - 1 or
						hex.row == last_hex_row + 3 and hex.column == last_hex_column - 2 or
						hex.row == last_hex_row + 4 and hex.column == last_hex_column - 2
				  ):
					line_left.append(hex)
				elif (
						hex.row == last_hex_row - 1 and hex.column == last_hex_column or
						hex.row == last_hex_row - 2 and hex.column == last_hex_column + 1 or
						hex.row == last_hex_row - 3 and hex.column == last_hex_column + 1 or
						hex.row == last_hex_row - 4 and hex.column == last_hex_column + 2
					):
					line_right.append(hex)

		line_left.sort(key=lambda x: x.row)

		line_right.sort(key=lambda x: x.row)
		line_right.reverse()

		return self.check_if_five_in_line(line_left, line_right)


	def check_line_descending(self):
		last_hex_row = self.last_move_hex.row
		last_hex_column = self.last_move_hex.column

		line_left = []
		line_right = []
		#odd row number
		if last_hex_row % 2 != 0: 
			for hex in BoardState.valid_hexagons:
				if (
						hex.row == last_hex_row + 1 and hex.column == last_hex_column + 1 or
						hex.row == last_hex_row + 2 and hex.column == last_hex_column + 1 or
						hex.row == last_hex_row + 3 and hex.column == last_hex_column + 2 or
						hex.row == last_hex_row + 4 and hex.column == last_hex_column + 2
				  ):
					line_right.append(hex)
				elif (
						hex.row == last_hex_row - 1 and hex.column == last_hex_column or
						hex.row == last_hex_row - 2 and hex.column == last_hex_column - 1 or
						hex.row == last_hex_row - 3 and hex.column == last_hex_column - 1 or
						hex.row == last_hex_row - 4 and hex.column == last_hex_column - 2
					):
					line_left.append(hex)
		#even row number
		else: 
			for hex in BoardState.valid_hexagons:
				if (
						hex.row == last_hex_row + 1 and hex.column == last_hex_column or
						hex.row == last_hex_row + 2 and hex.column == last_hex_column + 1 or
						hex.row == last_hex_row + 3 and hex.column == last_hex_column + 1 or
						hex.row == last_hex_row + 4 and hex.column == last_hex_column + 2
				  ):
					line_right.append(hex)
				elif (
						hex.row == last_hex_row - 1 and hex.column == last_hex_column - 1 or
						hex.row == last_hex_row - 2 and hex.column == last_hex_column - 1 or
						hex.row == last_hex_row - 3 and hex.column == last_hex_column - 2 or
						hex.row == last_hex_row - 4 and hex.column == last_hex_column - 2
					):
					line_left.append(hex)

		line_left.sort(key=lambda x: x.row)
		line_left.reverse()

		line_right.sort(key=lambda x: x.row)
		
		return self.check_if_five_in_line(line_left, line_right)


	def check_if_five_in_line(self, line_left, line_right):
		last_move_player_hexagons = self.player2_hexagons if self.current_player == PLAYER_1 else self.player1_hexagons
		line_counter = 1

		for hex in line_left:
			if hex in last_move_player_hexagons:
				line_counter += 1
			else: 
				break

		if line_counter == 5:
			return line_counter

		for hex in line_right:
			if hex in last_move_player_hexagons:
				line_counter += 1
				if line_counter == 5:
					return line_counter
			else: 
				break
				
		return line_counter


	def check_if_enclosing(self):
		currently_considered = self.last_move_hex

		if currently_considered == None: #For check_if_win when initializing the first state
			return False

		open_list = []
		closed_list = []

		while True:
			can_see_border_list = []
			considered_neighbours = []
			neighbours = self.get_hexagon_neighbours(currently_considered)

			# restrict considered neighbours
			for n in neighbours:
				# (first line of the condition) last move belongs to player 1
				if (self.current_player == PLAYER_2 and n in self.player1_hexagons) or \
				   (self.current_player == PLAYER_1 and n in self.player2_hexagons):
				   	continue

				if self.check_if_can_see_the_border(n):
					can_see_border_list.append(n)
					continue

				if n in closed_list:
					continue

				considered_neighbours.append(n)
			
			to_be_removed_hexes = []

			# gather the candidates neighbours of whom can see the border of the board
			for cn in considered_neighbours:
				for n in self.get_hexagon_neighbours(cn):
					if n in can_see_border_list:
						to_be_removed_hexes.append(cn)

			# discard the candidates gathered above
			for tbr in to_be_removed_hexes:
				if tbr in considered_neighbours: #Extra Sanity check
					considered_neighbours.remove(tbr)

			open_list.extend(considered_neighbours)
			closed_list.append(currently_considered)	

			if len(open_list) == 0:
				break

			currently_considered = open_list.pop(0)

		closed_list.pop(0)

		# At least one white enclosed
		if len(closed_list) > 0 and self.current_player == PLAYER_2:
			for hex in closed_list:
				if hex in self.player2_hexagons:
					return True
			return False

		# At least one black enclosed
		elif len(closed_list) > 0 and self.current_player == PLAYER_1:
			for hex in closed_list:
				if hex in self.player1_hexagons:
					return True
			return False

		else:
			return False


	def check_if_can_see_the_border(self, current_hex):
		if self.check_side_of_direction(current_hex, DIRECTION_LEFT):
			return True

		if self.check_side_of_direction(current_hex, DIRECTION_UPPER_LEFT):
			return True

		if self.check_side_of_direction(current_hex, DIRECTION_UPPER_RIGHT):
			return True

		if self.check_side_of_direction(current_hex, DIRECTION_RIGHT):
			return True

		if self.check_side_of_direction(current_hex, DIRECTION_BOTTOM_RIGHT):
			return True

		if self.check_side_of_direction(current_hex, DIRECTION_BOTTOM_LEFT):
			return True

		return False


	def check_side_of_direction(self, current_hex, direction):
		current_hex_row = current_hex.row
		current_hex_column = current_hex.column

		while True:
			#Single Step
			current_hex_row, current_hex_column = self.determine_next_hex_coordinates(current_hex_row, current_hex_column, direction)

			considered_hexagon = None

			for hex in BoardState.valid_hexagons:
				if (hex.row == current_hex_row and hex.column == current_hex_column):
					considered_hexagon = hex
					break

			if considered_hexagon == None: #It means that the border has been reached
				return True 

			# Since it's the enclosing condtion: current player different than playerN_hexagons)
			# Current p2, so last move belongs to p1. We consider "blocking the visibility" as p1 blocking view of p2
			if (self.current_player == PLAYER_2 and considered_hexagon in self.player1_hexagons) or \
			   (self.current_player == PLAYER_1 and considered_hexagon in self.player2_hexagons):
				return False


	def determine_next_hex_coordinates(self, current_row, current_column, direction):
		if direction == DIRECTION_LEFT:
			return (current_row, current_column - 1)

		if direction == DIRECTION_RIGHT:
			return (current_row, current_column + 1)

		if direction == DIRECTION_UPPER_LEFT:
			if current_row %2 == 0:
				current_column -= 1
			return (current_row - 1, current_column)

		if direction == DIRECTION_UPPER_RIGHT:
			if current_row %2 != 0:
				current_column += 1
			return (current_row - 1, current_column)

		if direction == DIRECTION_BOTTOM_LEFT:
			if current_row %2 == 0:
				current_column -= 1
			return (current_row + 1, current_column)

		if direction == DIRECTION_BOTTOM_RIGHT:
			if current_row %2 != 0:
				current_column += 1
			return (current_row + 1, current_column)

		return (current_row, current_column)
