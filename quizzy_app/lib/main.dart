import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'screens/settings_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const QuizzyApp());
}

class QuizzyApp extends StatelessWidget {
  const QuizzyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Quizzy AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6C63FF),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      home: const HomeScreen(),
      routes: {
        '/settings': (context) => const SettingsScreen(),
      },
    );
  }
}
