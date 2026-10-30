import 'package:flutter/material.dart';

class ResultScreen extends StatelessWidget {
  final int score;
  final int total;
  final List<Map<String, dynamic>> results;
  final String title;

  const ResultScreen({
    super.key,
    required this.score,
    required this.total,
    required this.results,
    required this.title,
  });

  double get percentage => total > 0 ? score / total : 0;

  String get grade {
    if (percentage >= 0.9) return 'A+ 🏆';
    if (percentage >= 0.8) return 'A 🌟';
    if (percentage >= 0.7) return 'B 👍';
    if (percentage >= 0.6) return 'C 📚';
    return 'D — Keep Practicing 💪';
  }

  Color get gradeColor {
    if (percentage >= 0.8) return Colors.greenAccent;
    if (percentage >= 0.6) return Colors.orangeAccent;
    return Colors.redAccent;
  }

  List<String> get weakConcepts {
    final wrongAnswers = results.where((r) => r['isCorrect'] == false);
    final concepts = wrongAnswers.map((r) => r['concept'] as String).where((c) => c.isNotEmpty).toSet().toList();
    return concepts;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F0F1A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1A1A2E),
        title: const Text('Quiz Results 🏆', style: TextStyle(color: Colors.white)),
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Score card
            Container(
              width: double.infinity,
              margin: const EdgeInsets.all(20),
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFF6C63FF).withOpacity(0.8),
                    const Color(0xFF48CAE4).withOpacity(0.8),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  Text(
                    grade,
                    style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.baseline,
                    textBaseline: TextBaseline.alphabetic,
                    children: [
                      Text(
                        '$score',
                        style: const TextStyle(fontSize: 56, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                      Text(
                        ' / $total',
                        style: const TextStyle(fontSize: 24, color: Colors.white70),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${(percentage * 100).round()}% Correct',
                    style: const TextStyle(fontSize: 16, color: Colors.white70),
                  ),
                  const SizedBox(height: 16),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: LinearProgressIndicator(
                      value: percentage,
                      backgroundColor: Colors.white24,
                      valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
                      minHeight: 8,
                    ),
                  ),
                ],
              ),
            ),

            // Weak concepts
            if (weakConcepts.isNotEmpty) ...[
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.orange.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.orangeAccent.withOpacity(0.4)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.lightbulb_outline, color: Colors.orangeAccent, size: 18),
                          SizedBox(width: 6),
                          Text('Review These Topics', style: TextStyle(color: Colors.orangeAccent, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 4,
                        children: weakConcepts.map((c) => Chip(
                          label: Text(c, style: const TextStyle(fontSize: 12, color: Colors.white)),
                          backgroundColor: Colors.orange.withOpacity(0.2),
                          side: BorderSide(color: Colors.orangeAccent.withOpacity(0.5)),
                          padding: EdgeInsets.zero,
                        )).toList(),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Q&A review list
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                itemCount: results.length,
                itemBuilder: (context, index) {
                  final r = results[index];
                  final isCorrect = r['isCorrect'] as bool;
                  return Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: isCorrect ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isCorrect ? Colors.greenAccent.withOpacity(0.4) : Colors.redAccent.withOpacity(0.4),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              isCorrect ? Icons.check_circle : Icons.cancel,
                              color: isCorrect ? Colors.greenAccent : Colors.redAccent,
                              size: 18,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              'Q${index + 1}',
                              style: TextStyle(
                                color: isCorrect ? Colors.greenAccent : Colors.redAccent,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(
                          r['question'] as String,
                          style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4),
                        ),
                        if (!isCorrect) ...[
                          const SizedBox(height: 6),
                          Text(
                            'Your answer: ${r['userAnswer']}',
                            style: const TextStyle(color: Colors.redAccent, fontSize: 12),
                          ),
                          Text(
                            'Correct: ${r['correctAnswer']}',
                            style: const TextStyle(color: Colors.greenAccent, fontSize: 12),
                          ),
                        ],
                        if ((r['explanation'] as String).isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            r['explanation'] as String,
                            style: const TextStyle(color: Colors.white54, fontSize: 12, height: 1.3),
                          ),
                        ],
                      ],
                    ),
                  );
                },
              ),
            ),

            // Bottom buttons
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
                      icon: const Icon(Icons.mic),
                      label: const Text('Record Again'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF6C63FF),
                        side: const BorderSide(color: Color(0xFF6C63FF)),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
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
}

