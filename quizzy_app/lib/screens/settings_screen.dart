import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final TextEditingController _urlController = TextEditingController();
  bool _isSaving = false;
  bool _isTesting = false;
  String _testResult = '';

  @override
  void initState() {
    super.initState();
    _loadUrl();
  }

  Future<void> _loadUrl() async {
    final url = await ApiService.getBackendUrl();
    _urlController.text = url == ApiService.defaultUrl ? '' : url;
  }

  Future<void> _save() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a URL'), behavior: SnackBarBehavior.floating),
      );
      return;
    }
    if (!url.startsWith('http')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('URL must start with http:// or https://'), behavior: SnackBarBehavior.floating),
      );
      return;
    }
    setState(() => _isSaving = true);
    await ApiService.setBackendUrl(url);
    setState(() => _isSaving = false);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('✅ Saved!'), behavior: SnackBarBehavior.floating),
    );
  }

  Future<void> _testConnection() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;
    await ApiService.setBackendUrl(url);

    setState(() {
      _isTesting = true;
      _testResult = '';
    });

    final ok = await ApiService.checkHealth();
    setState(() {
      _isTesting = false;
      _testResult = ok ? '✅ Connected to backend!' : '❌ Could not reach backend. Check the URL.';
    });
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F0F1A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1A1A2E),
        title: const Text('Settings ⚙️', style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white70),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Backend URL',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 6),
            const Text(
              'Enter your Render deployment URL (the same server that powers the Quizzy web app).',
              style: TextStyle(color: Colors.white54, fontSize: 13, height: 1.5),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _urlController,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'https://your-app.onrender.com',
                hintStyle: const TextStyle(color: Colors.white30),
                filled: true,
                fillColor: const Color(0xFF1E1E2E),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Color(0xFF6C63FF)),
                ),
                prefixIcon: const Icon(Icons.link, color: Colors.white38),
              ),
              keyboardType: TextInputType.url,
              autocorrect: false,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isSaving ? null : _save,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF6C63FF),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: _isSaving
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Save', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton(
                    onPressed: _isTesting ? null : _testConnection,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF48CAE4),
                      side: const BorderSide(color: Color(0xFF48CAE4)),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: _isTesting
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF48CAE4)),
                          )
                        : const Text('Test Connection', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ),
              ],
            ),
            if (_testResult.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _testResult.startsWith('✅') ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _testResult.startsWith('✅') ? Colors.greenAccent.withOpacity(0.5) : Colors.redAccent.withOpacity(0.5),
                  ),
                ),
                child: Text(
                  _testResult,
                  style: TextStyle(
                    color: _testResult.startsWith('✅') ? Colors.greenAccent : Colors.redAccent,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
            const SizedBox(height: 32),
            const Divider(color: Colors.white12),
            const SizedBox(height: 16),
            const Text(
              'How it works',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
            ),
            const SizedBox(height: 12),
            _infoRow(Icons.mic, 'Record your voice — any lecture, topic or notes'),
            _infoRow(Icons.auto_awesome, 'Transcript is sent to your Quizzy backend'),
            _infoRow(Icons.psychology, 'Gemini AI generates a smart quiz from your content'),
            _infoRow(Icons.quiz, 'Answer MCQ or fill-in-the-blank questions'),
            _infoRow(Icons.bar_chart, 'Get instant feedback and a score breakdown'),
          ],
        ),
      ),
    );
  }

  Widget _infoRow(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Icon(icon, size: 18, color: const Color(0xFF6C63FF)),
          const SizedBox(width: 10),
          Expanded(child: Text(text, style: const TextStyle(color: Colors.white60, fontSize: 13))),
        ],
      ),
    );
  }
}

