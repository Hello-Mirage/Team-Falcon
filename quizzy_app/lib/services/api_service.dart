import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/question.dart';

class ApiService {
  static const String _prefKeyUrl = 'backend_url';
  static const String defaultUrl = 'https://YOUR-APP.onrender.com';

  static Future<String> getBackendUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_prefKeyUrl) ?? defaultUrl;
  }

  static Future<void> setBackendUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKeyUrl, url.trim().replaceAll(RegExp(r'/$'), ''));
  }

  static Future<List<Question>> generateQuiz({
    required String content,
    String title = 'Voice Quiz',
    int count = 5,
    String questionType = 'mixed',
  }) async {
    final baseUrl = await getBackendUrl();

    final response = await http
        .post(
          Uri.parse('$baseUrl/api/quiz'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'title': title,
            'content': content,
            'question_type': questionType,
            'count': count,
            'timer_seconds': 30,
          }),
        )
        .timeout(const Duration(seconds: 60));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final List<dynamic> questionsJson = data['questions'] ?? [];
      if (questionsJson.isEmpty) {
        throw Exception('No questions returned. Try a longer or more detailed recording.');
      }
      return questionsJson.map((q) => Question.fromJson(q)).toList();
    } else {
      String errMsg = 'Server error ${response.statusCode}';
      try {
        final err = jsonDecode(response.body);
        errMsg = err['error'] ?? errMsg;
      } catch (_) {}
      throw Exception(errMsg);
    }
  }

  static Future<bool> checkHealth() async {
    try {
      final baseUrl = await getBackendUrl();
      final response = await http
          .get(Uri.parse('$baseUrl/api/health'))
          .timeout(const Duration(seconds: 10));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}

