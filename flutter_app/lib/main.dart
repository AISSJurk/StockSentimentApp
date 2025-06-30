import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:syncfusion_flutter_gauges/gauges.dart';

import 'stock_detail_page.dart';
import 'market_detail_page.dart';
import 'settings_page.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs       = await SharedPreferences.getInstance();
  final useLocalApi = prefs.getBool('useLocalApi') ?? true;
  runApp(SentimentApp(useLocalApi: useLocalApi));
}

class SentimentApp extends StatefulWidget {
  final bool useLocalApi;
  const SentimentApp({Key? key, required this.useLocalApi}) : super(key: key);

  @override
  State<SentimentApp> createState() => _SentimentAppState();
}

class _SentimentAppState extends State<SentimentApp> {
  late bool _useLocalApi;

  @override
  void initState() {
    super.initState();
    _useLocalApi = widget.useLocalApi;
  }

  Future<void> _toggleUseLocalApi(bool on) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('useLocalApi', on);
    setState(() => _useLocalApi = on);
  }

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(seedColor: Colors.teal);
    return MaterialApp(
      title: 'Market Mood Meter',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: scheme,
        scaffoldBackgroundColor: scheme.surface,
        cardTheme: const CardThemeData(
          elevation: 6,
          margin: EdgeInsets.symmetric(vertical: 8, horizontal: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(16)),
          ),
        ),
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => TopMoversPage(useLocalApi: _useLocalApi),
        '/settings': (_) => SettingsPage(
              useLocalApi: _useLocalApi,
              onToggle: _toggleUseLocalApi,
            ),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/stock') {
          final symbol = settings.arguments as String;
          return MaterialPageRoute(
            builder: (_) => StockDetailPage(symbol: symbol),
          );
        } else if (settings.name == '/market') {
          final days = settings.arguments as int;
          return MaterialPageRoute(
            builder: (_) => MarketDetailPage(initialDays: days),
          );
        }
        return null;
      },
    );
  }
}

class TopMoversPage extends StatefulWidget {
  final bool useLocalApi;
  const TopMoversPage({Key? key, required this.useLocalApi}) : super(key: key);

  @override
  State<TopMoversPage> createState() => _TopMoversPageState();
}

class _TopMoversPageState extends State<TopMoversPage> {
  Map<String, dynamic>? topPositive, topNegative;
  List<dynamic> restPositive = [], restNegative = [];
  Set<String> expandedMessages = {};
  bool _loading = false;
  String? _error;
  DateTime? _lastUpdated;
  double? _marketMood, _marketConfidence;
  String? _dataVersion, _dataGeneratedAt;

  @override
  void initState() {
    super.initState();
    _fetchTopMovers();
  }

  Future<void> _fetchTopMovers() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final baseUrl = widget.useLocalApi
          ? 'http://192.168.1.229:8000'
          : 'https://your-deployed-url.com';
      final res = await http.get(Uri.parse('$baseUrl/top-movers'));
      if (res.statusCode != 200) throw Exception('Error ${res.statusCode}');
      final data = json.decode(res.body);

      _marketMood       = (data['market_mood']      as num?)?.toDouble();
      _marketConfidence = (data['market_confidence']as num?)?.toDouble();
      _lastUpdated      = DateTime.now();
      _dataVersion      = data['version']     as String?;
      _dataGeneratedAt  = data['generated_at']as String?;
      topPositive  = data['top_positive'];
      topNegative  = data['top_negative'];
      restPositive = data['rest_positive'] ?? [];
      restNegative = data['rest_negative'] ?? [];
    } catch (e) {
      _error = e.toString();
    } finally {
      setState(() { _loading = false; });
    }
  }

  String _formatDateTime(DateTime dt) {
    final l = dt.toLocal();
    return '${l.month}/${l.day}/${l.year} '
           '${l.hour.toString().padLeft(2, '0')}:'
           '${l.minute.toString().padLeft(2, '0')}';
  }

  Widget buildMarketGauge(double mood, double confidence) {
    final displayValue = mood.clamp(0.0, 1.0);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("📊 Market Mood",
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            SizedBox(
              height: 160,
              child: SfRadialGauge(axes: [
                RadialAxis(
                  minimum: 0, maximum: 1,
                  showLabels: false, showTicks: false,
                  pointers: [
                    RangePointer(
                      value: 1,
                      width: 15,
                      enableAnimation: false,
                      gradient: const SweepGradient(
                        startAngle: 180, endAngle: 360,
                        colors: [Colors.red, Colors.yellow, Colors.green],
                        stops: [0.0, 0.5, 1.0],
                      ),
                    ),
                    NeedlePointer(
                      value: displayValue,
                      needleColor: Colors.black,
                      enableAnimation: true,
                      animationType: AnimationType.ease,
                      animationDuration: 1500,
                    ),
                  ],
                  annotations: [
                    GaugeAnnotation(
                      angle: 90,
                      positionFactor: 0.5,
                      widget: Text(
                        'Mood: ${(displayValue * 100).toInt()}%',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                  ],
                ),
              ]),
            ),
            const SizedBox(height: 12),
            Text(
              "Confidence: ${(confidence * 100).toInt()}%",
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 4),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final fullWidth = constraints.maxWidth;
                  final tickX = fullWidth * confidence;
                  return Stack(
                    children: [
                      Container(
                        height: 8,
                        decoration: const BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Colors.red, Colors.yellow, Colors.green],
                            stops: [0.0, 0.5, 1.0],
                          ),
                        ),
                      ),
                      Align(
                        alignment: Alignment.centerRight,
                        child: FractionallySizedBox(
                          widthFactor: 1 - confidence,
                          child: Container(
                            color: Colors.grey.shade300,
                            height: 8,
                          ),
                        ),
                      ),
                      Positioned(
                        left: tickX - 1,
                        top: 0,
                        bottom: 0,
                        child: Container(width: 2, color: Colors.black),
                      ),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget buildGauge(String symbol, double mood, double confidence, bool isPositive) {
    final displayValue = isPositive
        ? mood.clamp(0.0, 1.0)
        : (-mood).clamp(0.0, 1.0);
    final gradient = isPositive
        ? const SweepGradient(
            startAngle: 180, endAngle: 360,
            colors: [Colors.red, Colors.yellow, Colors.green],
            stops: [0.0, 0.5, 1.0],
          )
        : const SweepGradient(
            startAngle: 180, endAngle: 360,
            colors: [Colors.green, Colors.yellow, Colors.red],
            stops: [0.0, 0.5, 1.0],
          );
    return Card(
      color: isPositive ? Colors.lightGreen.shade50 : Colors.red.shade50,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              isPositive ? "🚀 $symbol" : "📉 $symbol",
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 140,
              child: SfRadialGauge(axes: [
                RadialAxis(
                  minimum: 0, maximum: 1,
                  showLabels: false, showTicks: false,
                  pointers: [
                    RangePointer(
                      value: 1.0,
                      width: 12,
                      enableAnimation: false,
                      gradient: gradient,
                    ),
                    NeedlePointer(
                      value: displayValue,
                      needleColor: Colors.black,
                      enableAnimation: true,
                      animationType: AnimationType.ease,
                      animationDuration: 1500,
                    ),
                  ],
                  annotations: [
                    GaugeAnnotation(
                      angle: 90,
                      positionFactor: 0.4,
                      widget: Text(
                        'Mood: ${(mood * 100).toInt()}%',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                  ],
                ),
              ]),
            ),
          ],
        ),
      ),
    );
  }

  Widget buildMiniStockList(List<dynamic> stocks, bool isPositive) {
    final limited = stocks.take(5).toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: limited.map((s) {
        final sym = s['symbol'] as String;
        final mood = (s['mood_score'] as num).toDouble();
        final conf = (s['confidence'] as num).toDouble();
        final rawMsgs = List<Map<String, dynamic>>.from(s['messages'] as List);
        final seen = <String>{};
        final msgs = <Map<String, dynamic>>[];
        for (var m in rawMsgs) {
          if (seen.add(m['text'] as String)) msgs.add(m);
        }
        final id = '$sym\_${limited.indexOf(s)}';
        final expanded = expandedMessages.contains(id);
        return Card(
          child: InkWell(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => StockDetailPage(symbol: sym),
                ),
              );
            },
            onLongPress: () => setState(() {
              expanded
                  ? expandedMessages.remove(id)
                  : expandedMessages.add(id);
            }),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [  
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(sym, style: Theme.of(context).textTheme.bodyLarge),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text('Mood: ${mood.toStringAsFixed(2)}',
                              style: Theme.of(context).textTheme.bodySmall),
                          Text('Conf: ${(conf * 100).toInt()}%',
                              style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    ],
                  ),
                  if (expanded) ...[
                    const SizedBox(height: 8),
                    for (var m in msgs) ...[
                      Text('• ${m['text']} — by ${m['author']}', 
                          style: Theme.of(context).textTheme.bodySmall),
                      Text('Score: ${m['score']}   Label: ${m['intensity']}', 
                          style: Theme.of(context).textTheme.labelSmall),
                      const SizedBox(height: 6),
                    ],
                  ],
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget buildColumn({
    required Map<String, dynamic> stock,
    required List<dynamic> rest,
    required bool isPositive,
  }) {
    final sym    = stock['symbol'] as String;
    final rawHl  = List<Map<String, dynamic>>.from(stock['messages'] as List);
    final seenHl = <String>{};
    final headlines = <Map<String, dynamic>>[];
    for (var m in rawHl) {
      if (seenHl.add(m['text'] as String)) headlines.add(m);
    }
    final id       = '${sym}_headline';
    final expanded = expandedMessages.contains(id);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          child: InkWell(
            onTap: () => setState(() {
              expanded
                  ? expandedMessages.remove(id)
                  : expandedMessages.add(id);
            }),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Top Headlines',
                      style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 6),
                  for (var m in headlines.take(expanded ? 5 : 1)) ...[
                    Text('• ${m['text']}', style: Theme.of(context).textTheme.bodySmall),
                    const SizedBox(height: 6),
                  ],
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        buildMiniStockList(rest, isPositive),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Market Mood Meter'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchTopMovers,
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Text(
                    'Error: $_error\nTap to retry',
                    textAlign: TextAlign.center,
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _fetchTopMovers,
                  child: ListView(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    children: [
                      if (_lastUpdated != null)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: Text(
                            'Last updated: ${_formatDateTime(_lastUpdated!)}',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ),
                      if (_marketMood != null && _marketConfidence != null)
                        GestureDetector(
                          onTap: () => Navigator.pushNamed(context, '/market', arguments: 7),
                          child: buildMarketGauge(_marketMood!, _marketConfidence!),
                        ),
                      const SizedBox(height: 16),
                      if (topPositive != null && topNegative != null) ...[
                        Row(
                          children: [
                            Expanded(
                              child: GestureDetector(
                                onTap: () => Navigator.pushNamed(context, '/stock', arguments: topPositive!['symbol']),
                                child: buildGauge(
                                  topPositive!['symbol'] as String,
                                  (topPositive!['mood_score'] as num).toDouble(),
                                  (topPositive!['confidence'] as num).toDouble(),
                                  true,
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: GestureDetector(
                                onTap: () => Navigator.pushNamed(context, '/stock', arguments: topNegative!['symbol']),
                                child: buildGauge(
                                  topNegative!['symbol'] as String,
                                  (topNegative!['mood_score'] as num).toDouble(),
                                  (topNegative!['confidence'] as num).toDouble(),
                                  false,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                      const SizedBox(height: 24),
                      if (topPositive != null && topNegative != null)
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: buildColumn(stock: topPositive! as Map<String, dynamic>, rest: restPositive, isPositive: true),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: buildColumn(stock: topNegative! as Map<String, dynamic>, rest: restNegative, isPositive: false),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
    );
  }
}
