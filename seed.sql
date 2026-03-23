-- ============================================
-- Smart Quiz — Sample Questions
-- ============================================

USE smart_quiz;

-- ----------------------------
-- EASY Questions (5)
-- ----------------------------
INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_ans, difficulty, category) VALUES
('What does HTML stand for?',
 'Hyper Text Markup Language', 'High Tech Modern Language', 'Hyper Transfer Markup Language', 'Home Tool Markup Language',
 'a', 'easy', 'web'),

('Which language is used for styling web pages?',
 'HTML', 'CSS', 'Python', 'Java',
 'b', 'easy', 'web'),

('What does CPU stand for?',
 'Central Process Unit', 'Central Processing Unit', 'Computer Personal Unit', 'Central Processor Utility',
 'b', 'easy', 'general'),

('Which of the following is a Python data type?',
 'paragraph', 'dictionary', 'module', 'function',
 'b', 'easy', 'python'),

('What symbol is used for comments in Python?',
 '//', '--', '#', '/* */',
 'c', 'easy', 'python');

-- ----------------------------
-- MEDIUM Questions (5)
-- ----------------------------
INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_ans, difficulty, category) VALUES
('What is the output of: print(type(10))?',
 '<class ''float''>', '<class ''int''>', '<class ''str''>', '<class ''number''>',
 'b', 'medium', 'python'),

('In Flask, which decorator is used to define a route?',
 '@app.route()', '@flask.path()', '@route.add()', '@app.url()',
 'a', 'medium', 'web'),

('Which SQL keyword is used to retrieve data from a database?',
 'GET', 'FETCH', 'SELECT', 'RETRIEVE',
 'c', 'medium', 'general'),

('What is the default port number for Flask development server?',
 '8080', '3000', '5000', '8000',
 'c', 'medium', 'web'),

('Which HTTP method is typically used to submit form data?',
 'GET', 'POST', 'PUT', 'PATCH',
 'b', 'medium', 'web');

-- ----------------------------
-- HARD Questions (5)
-- ----------------------------
INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_ans, difficulty, category) VALUES
('What is the time complexity of binary search?',
 'O(n)', 'O(n log n)', 'O(log n)', 'O(1)',
 'c', 'hard', 'general'),

('In Python, what does the GIL stand for?',
 'Global Interpreter Lock', 'General Input Lock', 'Global Index Loop', 'Generated Interpreter Layer',
 'a', 'hard', 'python'),

('Which data structure uses LIFO (Last In, First Out)?',
 'Queue', 'Array', 'Stack', 'Linked List',
 'c', 'hard', 'general'),

('What does the "yield" keyword do in Python?',
 'Stops the function permanently', 'Returns a value and pauses the function', 'Deletes a variable', 'Creates a new thread',
 'b', 'hard', 'python'),

('In SQL, what is the difference between WHERE and HAVING?',
 'No difference', 'WHERE filters rows, HAVING filters groups', 'HAVING filters rows, WHERE filters groups', 'WHERE is for UPDATE only',
 'b', 'hard', 'general');
