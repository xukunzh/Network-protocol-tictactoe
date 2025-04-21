import unittest


# Function to check if a player has won
def check_win(board, sym):
    # Winning lines: 3 rows, 3 columns, 2 diagonals
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
        (0, 4, 8), (2, 4, 6)  # diagonals
    ]
    for a, b, c in lines:
        if board[a] == board[b] == board[c] == sym:
            return True
    return False


# Function to validate whether a move is allowed
def is_valid_move(room, pid, idx, sym):
    if not room or sym is None or idx is None or idx < 0 or idx >= 9:
        return False
    if room['board'][idx]:
        return False  # cell is already occupied
    if room['turn'] != pid:
        return False  # not this player's turn
    return True


class TestGameLogic(unittest.TestCase):
    # Tests for win detection

    def test_win_row(self):
        board = ['X', 'X', 'X', '', '', '', '', '', '']
        self.assertTrue(check_win(board, 'X'))

    def test_win_column(self):
        board = ['O', '', '', 'O', '', '', 'O', '', '']
        self.assertTrue(check_win(board, 'O'))

    def test_win_diagonal(self):
        board = ['X', '', '', '', 'X', '', '', '', 'X']
        self.assertTrue(check_win(board, 'X'))

    def test_no_win(self):
        board = ['X', '', 'X', 'X', 'O', 'O', 'O', 'X', 'X']
        self.assertFalse(check_win(board, 'X'))
        self.assertFalse(check_win(board, 'O'))

    # -------- Tests for move validation --------

    def test_valid_move(self):
        room = {'board': [''] * 9, 'turn': '1'}
        self.assertTrue(is_valid_move(room, '1', 0, 'X'))

    def test_invalid_turn(self):
        room = {'board': [''] * 9, 'turn': '2'}
        self.assertFalse(is_valid_move(room, '1', 0, 'X'))

    def test_cell_occupied(self):
        room = {'board': ['X', '', '', '', '', '', '', '', ''], 'turn': '1'}
        self.assertFalse(is_valid_move(room, '1', 0, 'X'))

    def test_index_out_of_bounds(self):
        room = {'board': [''] * 9, 'turn': '1'}
        self.assertFalse(is_valid_move(room, '1', 10, 'X'))

    def test_missing_symbol(self):
        room = {'board': [''] * 9, 'turn': '1'}
        self.assertFalse(is_valid_move(room, '1', 0, None))

    def test_valid_move_player2(self):
        room = {'board': [''] * 9, 'turn': '2'}
        self.assertTrue(is_valid_move(room, '2', 4, 'O'))

    def test_wrong_turn_player2(self):
        room = {'board': [''] * 9, 'turn': '1'}
        self.assertFalse(is_valid_move(room, '2', 3, 'O'))


if __name__ == '__main__':
    unittest.main()
