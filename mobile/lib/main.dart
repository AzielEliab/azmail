import 'package:flutter/material.dart';

import 'theme.dart';

void main() {
  runApp(const AzMailApp());
}

class AzMailApp extends StatelessWidget {
  const AzMailApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AZMail',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: const AirlockPage(),
    );
  }
}

class DemoMessage {
  DemoMessage({
    required this.from,
    required this.subject,
    required this.body,
    required this.badge,
  });
  final String from;
  final String subject;
  final String body;
  final String badge;
}

class AirlockPage extends StatefulWidget {
  const AirlockPage({super.key});

  @override
  State<AirlockPage> createState() => _AirlockPageState();
}

class _AirlockPageState extends State<AirlockPage> {
  final _from = TextEditingController();
  final _subject = TextEditingController();
  final _body = TextEditingController();
  final _queue = <DemoMessage>[];
  String _status = 'airlock empty. mesh OFF. not an MTA.';

  @override
  void dispose() {
    _from.dispose();
    _subject.dispose();
    _body.dispose();
    super.dispose();
  }

  String _badgeFor(String from, String subject, String body) {
    final blob = '$from $subject $body'.toLowerCase();
    if (blob.contains('paypa1') ||
        blob.contains('g00gle') ||
        blob.contains('secure-paypal-login')) {
      return 'quarantined';
    }
    if (blob.contains('urgent') ||
        blob.contains('password') ||
        blob.contains('gift card')) {
      return 'high-risk';
    }
    if (from.contains('@') && !blob.contains('spf=pass')) {
      return 'unverified';
    }
    return 'verified';
  }

  void _receive() {
    final from = _from.text.trim();
    final subject = _subject.text.trim();
    final body = _body.text.trim();
    if (from.isEmpty) {
      setState(() => _status = 'from is required');
      return;
    }
    final badge = _badgeFor(from, subject, body);
    setState(() {
      _queue.add(DemoMessage(from: from, subject: subject, body: body, badge: badge));
      _status = 'classified $badge. confirm before treating as inbox.';
      _from.clear();
      _subject.clear();
      _body.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AZMail')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'No message is trusted until verified.',
            style: TextStyle(color: kGold, fontStyle: FontStyle.italic, fontSize: 16),
          ),
          const SizedBox(height: 8),
          const Text(
            'On-device APP 1.0 Mail Airlock. Advisory badges only. '
            'Does not send internet email. Mesh stays off on this scaffold.',
          ),
          const SizedBox(height: 16),
          TextField(controller: _from, decoration: const InputDecoration(labelText: 'From')),
          const SizedBox(height: 8),
          TextField(controller: _subject, decoration: const InputDecoration(labelText: 'Subject')),
          const SizedBox(height: 8),
          TextField(
            controller: _body,
            maxLines: 3,
            decoration: const InputDecoration(labelText: 'Body', alignLabelWithHint: true),
          ),
          const SizedBox(height: 12),
          FilledButton(onPressed: _receive, child: const Text('Receive into airlock')),
          const SizedBox(height: 12),
          Text(_status, style: const TextStyle(color: kGold)),
          const SizedBox(height: 16),
          for (var i = 0; i < _queue.length; i++)
            Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: SelectableText(
                  [
                    '#$i ${_queue[i].badge}',
                    _queue[i].from,
                    _queue[i].subject,
                    _queue[i].body,
                  ].join('\n'),
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 12, height: 1.4),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
