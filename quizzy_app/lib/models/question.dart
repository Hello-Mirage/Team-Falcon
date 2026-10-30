class Question {
  final String question;
  final String questionType; // 'mcq' or 'fill_blank'
  final List<String> options;
  final String correctAnswer;
  final String explanation;
  final String concept;
  final String difficulty;

  Question({
    required this.question,
    required this.questionType,
    required this.options,
    required this.correctAnswer,
    required this.explanation,
    required this.concept,
    required this.difficulty,
  });

  factory Question.fromJson(Map<String, dynamic> json) {
    return Question(
      question: json['question'] ?? '',
      questionType: json['question_type'] ?? 'mcq',
      options: List<String>.from(json['options'] ?? []),
      correctAnswer: (json['correct_answer'] ?? '').toString(),
      explanation: json['explanation'] ?? '',
      concept: json['concept'] ?? '',
      difficulty: json['difficulty'] ?? 'medium',
    );
  }
}

