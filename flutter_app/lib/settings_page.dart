import 'package:flutter/material.dart';

/// A simple settings screen to toggle between local and remote API endpoints.
class SettingsPage extends StatelessWidget {
  final bool useLocalApi;
  final ValueChanged<bool> onToggle;

  const SettingsPage({
    Key? key,
    required this.useLocalApi,
    required this.onToggle,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          SwitchListTile(
            title: const Text('Use Local Dev API'),
            subtitle: Text(
              useLocalApi
                  ? 'Local: http://192.168.1.229:8000'
                  : 'Remote: https://your-deployed-url.com',
            ),
            value: useLocalApi,
            onChanged: (value) {
              onToggle(value);
            },
          ),
          const SizedBox(height: 24),
          const Text(
            'Toggle this switch to switch between your local development API ' 
            'and the deployed production API. Your choice is saved ' 
            'and will persist across app restarts.',
            style: TextStyle(fontSize: 14),
          ),
        ],
      ),
    );
  }
}
