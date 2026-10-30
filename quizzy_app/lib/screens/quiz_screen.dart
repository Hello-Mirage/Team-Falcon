import 'package:flutter/material.dart';
import '../models/question.dart';
import 'result_screen.dart';

class QuizScreen extends StatefulWidget {
  final List<Question> questions;
  final String title;

  const QuizScreen({super.key, required this.questions, required this.title});

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> with SingleTickerProviderStateMixin {
  int _currentIndex = 0;
  String? _selectedAnswer;
  String _fillBlankAnswer = '';
  bool _answered = false;
  bool _isCorrect = false;
  int _score = 0;
  final List<Map<String, dynamic>> _results = [];
  final TextEditingController _textController = TextEditingController();
  late AnimationController _feedbackController;
  late Animation<double> _feedbackAnimation;

  @override
  void initState() {
    super.initState();
    _feedbackController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _feedbackAnimation = CurvedAnimation(parent: _feedbackController, curve: Curves.elasticOut);
  }

  Question get _currentQuestion => widget.questions[_currentIndex];

  void _submitAnswer() {
    if (_answered) return;

    final String userAnswer = _currentQuestion.questionType == 'fill_blank'
        ? _fillBlankAnswer.trim()
        : (_selectedAnswer ?? '');

    if (userAnswer.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select or type an answer'), behavior: SnackBarBehavior.floating),
      );
      return;
    }

    final correct = _checkAnswer(userAnswer);

    setState(() {
      _answered = true;
      _isCorrect = correct;
      if (correct) _score++;
    });

    _results.add({
      'question': _currentQuestion.question,
      'userAnswer': userAnswer,
      'correctAnswer': _currentQuestion.correctAnswer,
      'isCorrect': correct,
      'explanation': _currentQuestion.explanation,
      'concept': _currentQuestion.concept,
    });

    _feedbackController.forward(from: 0);
  }

  bool _checkAnswer(String userAnswer) {
    final correct = _currentQuestion.correctAnswer.toLowerCase().trim();
    final user = userAnswer.toLowerCase().trim();

    if (correct == user) return true;

    // For MCQ: check if user's answer starts with the same letter (A/B/C/D)
    if (_currentQuestion.questionType == 'mcq') {
      if (correct.isNotEmpty && user.isNotEmpty && correct[0] == user[0]) return true;
    }

    // For fill_blank: check if answer is contained
    if (_currentQuestion.questionType == 'fill_blank') {
      if (correct.contains(user) || user.contains(correct)) return true;
    }

    return false;
  }

  void _nextQuestion() {
    if (_currentIndex < widget.questions.length - 1) {
      setState(() {
        _currentIndex++;
        _selectedAnswer = null;
        _fillBlankAnswer = '';
        _answered = false;
        _isCorrect = false;
        _textController.clear();
      });
      _feedbackController.reverse();
    } else {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => ResultScreen(
            score: _score,
            total: widget.questions.length,
            results: _results,
            title: widget.title,
          ),
        ),
      );
    }
  }

  @override
  void dispose() {
    _feedbackController.dispose();
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final q = _currentQuestion;
    final progress = (_currentIndex + 1) / widget.questions.length;

    return Scaffold(
      backgroundColor: const Color(0xFF0F0F1A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1A1A2E),
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white70),
          onPressed: () => showDialog(
            context: context,
            builder: (ctx) => AlertDialog(
              backgroundColor: const Color(0xFF1E1E2E),
              title: const Text('Quit Quiz?', style: TextStyle(color: Colors.white)),
              content: const Text('Your progress will be lost.', style: TextStyle(color: Colors.white70)),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
                TextButton(
                  onPressed: () { Navigator.pop(ctx); Navigator.pop(context); },
                  child: const Text('Quit', style: TextStyle(color: Colors.redAccent)),
                ),
              ],
            ),
          ),
        ),
        title: Text(widget.title, style: const TextStyle(color: Colors.white, fontSize: 16)),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Text(
                '${_currentIndex + 1} / ${widget.questions.length}',
                style: const TextStyle(color: Colors.white60, fontWeight: FontWeight.w600),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Progress bar
            LinearProgressIndicator(
              value: progress,
              backgroundColor: Colors.white12,
              valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF6C63FF)),
              minHeight: 4,
            ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Concept + difficulty badge
                    if (q.concept.isNotEmpty || q.difficulty.isNotEmpty) ...[
                      Wrap(
                        spacing: 8,
                        children: [
                          if (q.concept.isNotEmpty)
                            Chip(
                              label: Text(q.concept, style: const TextStyle(fontSize: 11, color: Color(0xFF48CAE4))),
                              backgroundColor: const Color(0xFF1E1E2E),
                              side: const BorderSide(color: Color(0xFF48CAE4), width: 0.5),
                              padding: EdgeInsets.zero,
                            ),
                          if (q.difficulty.isNotEmpty)
                            Chip(
                              label: Text(q.difficulty.toUpperCase(), style: TextStyle(
                                fontSize: 10,
                                color: _difficultyColor(q.difficulty),
                                fontWeight: FontWeight.bold,
                              )),
                              backgroundColor: const Color(0xFF1E1E2E),
                              side: BorderSide(color: _difficultyColor(q.difficulty), width: 0.5),
                              padding: EdgeInsets.zero,
                            ),
                        ],
                      ),
                      const SizedBox(height: 12),
                    ],

                    // Question
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E1E2E),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: Text(
                        q.question,
                        style: const TextStyle(color: Colors.white, fontSize: 17, height: 1.5, fontWeight: FontWeight.w500),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Answer area
                    if (q.questionType == 'fill_blank') ...[
                      TextField(
                        controller: _textController,
                        enabled: !_answered,
                        style: const TextStyle(color: Colors.white),
                        decoration: InputDecoration(
                          hintText: 'Type your answer…',
                          hintStyle: const TextStyle(color: Colors.white38),
                          filled: true,
                          fillColor: const Color(0xFF1E1E2E),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: Color(0xFF6C63FF)),
                          ),
                        ),
                        onChanged: (val) => _fillBlankAnswer = val,
                        onSubmitted: (_) => _submitAnswer(),
                      ),
                    ] else ...[
                      ...q.options.asMap().entries.map((entry) {
                        final idx = entry.key;
                        final opt = entry.value;
                        final labels = ['A', 'B', 'C', 'D'];
                        final label = idx < labels.length ? labels[idx] : '${idx + 1}';
                        final isSelected = _selectedAnswer == opt;

                        Color borderColor = Colors.white12;
                        Color bgColor = const Color(0xFF1E1E2E);
                        Color textColor = Colors.white70;

                        if (_answered) {
                          final isCorrectOpt = opt.toLowerCase().trim() ==
                              q.correctAnswer.toLowerCase().trim() ||
                              (q.correctAnswer.isNotEmpty &&
                                  q.correctAnswer[0].toUpperCase() == label);
                          if (isCorrectOpt) {
                            borderColor = Colors.greenAccent;
                            bgColor = Colors.green.withOpacity(0.15);
                            textColor = Colors.greenAccent;
                          } else if (isSelected && !_isCorrect) {
                            borderColor = Colors.redAccent;
                            bgColor = Colors.red.withOpacity(0.15);
                            textColor = Colors.redAccent;
                          }
                        } else if (isSelected) {
                          borderColor = const Color(0xFF6C63FF);
                          bgColor = const Color(0xFF6C63FF).withOpacity(0.15);
                          textColor = Colors.white;
                        }

                        return Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: GestureDetector(
                            onTap: _answered ? null : () => setState(() => _selectedAnswer = opt),
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 200),
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: bgColor,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: borderColor, width: 1.5),
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    width: 28,
                                    height: 28,
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      color: isSelected && !_answered
                                          ? const Color(0xFF6C63FF)
                                          : Colors.white12,
                                    ),
                                    child: Center(
                                      child: Text(
                                        label,
                                        style: TextStyle(
                                          color: isSelected && !_answered ? Colors.white : Colors.white60,
                                          fontSize: 12,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Text(opt, style: TextStyle(color: textColor, fontSize: 15, height: 1.3)),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        );
                      }),
                    ],

                    const SizedBox(height: 12),

                    // Feedback
                    if (_answered) ...[
                      ScaleTransition(
                        scale: _feedbackAnimation,
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: _isCorrect
                                ? Colors.green.withOpacity(0.15)
                                : Colors.red.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: _isCorrect ? Colors.greenAccent : Colors.redAccent,
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(
                                    _isCorrect ? Icons.check_circle : Icons.cancel,
                                    color: _isCorrect ? Colors.greenAccent : Colors.redAccent,
                                    size: 20,
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    _isCorrect ? 'Correct! 🎉' : 'Incorrect',
                                    style: TextStyle(
                                      color: _isCorrect ? Colors.greenAccent : Colors.redAccent,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 15,
                                    ),
                                  ),
                                ],
                              ),
                              if (!_isCorrect) ...[
                                const SizedBox(height: 6),
                                Text(
                                  'Correct answer: ${q.correctAnswer}',
                                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                                ),
                              ],
                              if (q.explanation.isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Text(
                                  q.explanation,
                                  style: const TextStyle(color: Colors.white60, fontSize: 13, height: 1.4),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                  ],
                ),
              ),
            ),

            // Bottom buttons
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
              child: Row(
                children: [
                  if (!_answered)
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _submitAnswer,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF6C63FF),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                        ),
                        child: const Text('Submit Answer'),
                      ),
                    )
                  else
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _nextQuestion,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _isCorrect ? Colors.green : const Color(0xFF6C63FF),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                        ),
                        child: Text(
                          _currentIndex < widget.questions.length - 1 ? 'Next Question →' : 'See Results 🏆',
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _difficultyColor(String difficulty) {
    switch (difficulty.toLowerCase()) {
      case 'easy': return Colors.greenAccent;
      case 'hard': return Colors.redAccent;
      default: return Colors.orangeAccent;
    }
  }
}

