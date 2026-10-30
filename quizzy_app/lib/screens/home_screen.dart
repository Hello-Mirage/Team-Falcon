import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:permission_handler/permission_handler.dart';
import '../services/api_service.dart';
import 'quiz_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  final SpeechToText _speech = SpeechToText();
  final StringBuffer _transcript = StringBuffer();

  bool _isListening = false;
  bool _speechAvailable = false;
  bool _isGenerating = false;
  String _statusText = 'Press the mic to start recording';
  String _displayTranscript = '';
  int _questionCount = 5;

  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _initSpeech();
  }

  Future<void> _initSpeech() async {
    final available = await _speech.initialize(
      onError: (error) {
        setState(() {
          _statusText = 'Error: ${error.errorMsg}';
          if (_isListening) _stopListening();
        });
      },
      onStatus: (status) {
        if (status == 'done' && _isListening) {
          // Auto-restart to keep continuous recording
          _startListening();
        }
      },
    );
    setState(() => _speechAvailable = available);
  }

  Future<void> _toggleRecording() async {
    if (_isListening) {
      await _stopListening();
    } else {
      await _startListening();
    }
  }

  Future<void> _startListening() async {
    final status = await Permission.microphone.request();
    if (!status.isGranted) {
      _showSnack('Microphone permission required');
      return;
    }

    if (!_speechAvailable) {
      _showSnack('Speech recognition not available on this device');
      return;
    }

    setState(() {
      _isListening = true;
      _statusText = 'Listening… speak now';
    });

    await _speech.listen(
      onResult: (result) {
        setState(() {
          if (result.finalResult && result.recognizedWords.isNotEmpty) {
            if (_transcript.isNotEmpty) _transcript.write(' ');
            _transcript.write(result.recognizedWords);
          }
          final partialPreview = result.finalResult
              ? _transcript.toString()
              : '${_transcript.toString()} ${result.recognizedWords}'.trim();
          _displayTranscript = partialPreview;
        });
      },
      listenOptions: SpeechListenOptions(
        listenMode: ListenMode.dictation,
        partialResults: true,
      ),
    );
  }

  Future<void> _stopListening() async {
    await _speech.stop();
    setState(() {
      _isListening = false;
      _displayTranscript = _transcript.toString();
      _statusText = _transcript.isNotEmpty
          ? '✅ Recording complete! Ready to generate quiz.'
          : 'Recording stopped. Nothing captured.';
    });
  }

  void _clearTranscript() {
    setState(() {
      _transcript.clear();
      _displayTranscript = '';
      _statusText = 'Press the mic to start recording';
    });
  }

  Future<void> _generateQuiz() async {
    final content = _transcript.toString().trim();
    if (content.isEmpty) {
      _showSnack('Record some speech first!');
      return;
    }

    final url = await ApiService.getBackendUrl();
    if (!mounted) return;
    if (url == ApiService.defaultUrl || url.isEmpty) {
      _showSnack('Set your backend URL in Settings first ⚙️');
      Navigator.pushNamed(context, '/settings');
      return;
    }

    setState(() {
      _isGenerating = true;
      _statusText = '🤖 Generating quiz with Gemini AI…';
    });

    try {
      final questions = await ApiService.generateQuiz(
        content: content,
        title: 'Voice Quiz',
        count: _questionCount,
        questionType: 'mixed',
      );

      if (!mounted) return;

      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => QuizScreen(
            questions: questions,
            title: 'Voice Quiz',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      _showSnack('Error: ${e.toString().replaceFirst('Exception: ', '')}');
    } finally {
      if (mounted) {
        setState(() {
          _isGenerating = false;
          _statusText = _transcript.isNotEmpty
              ? '✅ Recording complete! Ready to generate quiz.'
              : 'Press the mic to start recording';
        });
      }
    }
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), behavior: SnackBarBehavior.floating),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _speech.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final hasTranscript = _displayTranscript.isNotEmpty;

    return Scaffold(
      backgroundColor: const Color(0xFF0F0F1A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1A1A2E),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF6C63FF), Color(0xFF48CAE4)],
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text('Q', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
            ),
            const SizedBox(width: 10),
            const Text('Quizzy AI', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings, color: Colors.white70),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
            tooltip: 'Settings',
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Status bar
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              color: const Color(0xFF1A1A2E),
              child: Text(
                _statusText,
                style: TextStyle(
                  color: _isListening ? const Color(0xFF48CAE4) : Colors.white60,
                  fontSize: 13,
                ),
                textAlign: TextAlign.center,
              ),
            ),

            // Transcript area
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Transcript', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w600)),
                        if (hasTranscript)
                          TextButton.icon(
                            onPressed: _clearTranscript,
                            icon: const Icon(Icons.clear, size: 16),
                            label: const Text('Clear'),
                            style: TextButton.styleFrom(foregroundColor: Colors.redAccent),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1E1E2E),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: _isListening ? const Color(0xFF6C63FF) : Colors.white12,
                            width: _isListening ? 2 : 1,
                          ),
                        ),
                        child: hasTranscript
                            ? SingleChildScrollView(
                                child: Text(
                                  _displayTranscript,
                                  style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.6),
                                ),
                              )
                            : const Center(
                                child: SingleChildScrollView(
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Icon(Icons.mic_none, size: 40, color: Colors.white24),
                                      SizedBox(height: 8),
                                      Text(
                                        'Your speech will appear here…\n\nSpeak naturally about any topic\nand Quizzy will turn it into a quiz!',
                                        textAlign: TextAlign.center,
                                        style: TextStyle(color: Colors.white38, height: 1.5),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Question count selector
                    Row(
                      children: [
                        const Text('Questions:', style: TextStyle(color: Colors.white60)),
                        const SizedBox(width: 12),
                        ...([3, 5, 7, 10].map((n) => Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ChoiceChip(
                            label: Text('$n'),
                            selected: _questionCount == n,
                            onSelected: (_) => setState(() => _questionCount = n),
                            selectedColor: const Color(0xFF6C63FF),
                            labelStyle: TextStyle(
                              color: _questionCount == n ? Colors.white : Colors.white60,
                              fontWeight: FontWeight.w600,
                            ),
                            backgroundColor: const Color(0xFF1E1E2E),
                            side: BorderSide(color: _questionCount == n ? const Color(0xFF6C63FF) : Colors.white12),
                          ),
                        ))),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            // Bottom controls
            Container(
              padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
              decoration: const BoxDecoration(
                color: Color(0xFF1A1A2E),
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: Column(
                children: [
                  // Mic button
                  AnimatedBuilder(
                    animation: _pulseAnimation,
                    builder: (context, child) {
                      return Transform.scale(
                        scale: _isListening ? _pulseAnimation.value : 1.0,
                        child: GestureDetector(
                          onTap: _isGenerating ? null : _toggleRecording,
                          child: Container(
                            width: 80,
                            height: 80,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: LinearGradient(
                                colors: _isListening
                                    ? [Colors.redAccent, Colors.red]
                                    : [const Color(0xFF6C63FF), const Color(0xFF48CAE4)],
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: (_isListening ? Colors.red : const Color(0xFF6C63FF)).withOpacity(0.4),
                                  blurRadius: 20,
                                  spreadRadius: 4,
                                ),
                              ],
                            ),
                            child: Icon(
                              _isListening ? Icons.stop : Icons.mic,
                              color: Colors.white,
                              size: 36,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _isListening ? 'Tap to stop' : 'Tap to record',
                    style: const TextStyle(color: Colors.white38, fontSize: 12),
                  ),
                  const SizedBox(height: 16),

                  // Generate quiz button
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: ElevatedButton.icon(
                      onPressed: (!hasTranscript || _isGenerating || _isListening) ? null : _generateQuiz,
                      icon: _isGenerating
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.auto_awesome),
                      label: Text(_isGenerating ? 'Generating Quiz…' : 'Generate Quiz ✨'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF6C63FF),
                        foregroundColor: Colors.white,
                        disabledBackgroundColor: Colors.white12,
                        disabledForegroundColor: Colors.white30,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
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

