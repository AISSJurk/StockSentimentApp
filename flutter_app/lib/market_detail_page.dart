import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:syncfusion_flutter_charts/charts.dart';
import 'package:intl/intl.dart';

class MarketDetailPage extends StatefulWidget {
  /// How many days to show initially (default to 7).
  final int initialDays;
  const MarketDetailPage({Key? key, this.initialDays = 7}) : super(key: key);

  @override
  State<MarketDetailPage> createState() => _MarketDetailPageState();
}

class _MarketDetailPageState extends State<MarketDetailPage> {
  late Future<List<HistoryPoint>> _futureHistory;
  late int _selectedDays;
  final List<int> _options = [7, 14, 30];

  @override
  void initState() {
    super.initState();
    _selectedDays = widget.initialDays;
    _futureHistory = _fetchHistory(_selectedDays);
  }

  Future<List<HistoryPoint>> _fetchHistory(int days) async {
    final uri = Uri.parse('http://127.0.0.1:8000/history/market?days=$days');
    final res = await http.get(uri);
    if (res.statusCode != 200) {
      throw Exception('Failed to load market history (${res.statusCode})');
    }
    final List jsonList = json.decode(res.body) as List;
    return jsonList.map((e) {
      return HistoryPoint(
        date: DateTime.parse(e['date'] as String),
        mood: (e['mood_score'] as num).toDouble(),
      );
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Market Mood History"),
      ),
      body: Column(
        children: [
          // ─── Days Toggle ───────────────────────────
          Padding(
            padding: const EdgeInsets.all(8),
            child: ToggleButtons(
              isSelected: _options.map((d) => d == _selectedDays).toList(),
              onPressed: (index) {
                setState(() {
                  _selectedDays = _options[index];
                  _futureHistory = _fetchHistory(_selectedDays);
                });
              },
              children: _options
                  .map((d) => Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        child: Text("$d days"),
                      ))
                  .toList(),
            ),
          ),

          // ─── Chart ─────────────────────────────────
          Expanded(
            child: FutureBuilder<List<HistoryPoint>>(
              future: _futureHistory,
              builder: (context, snap) {
                if (snap.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snap.hasError) {
                  return Center(child: Text('Error: \${snap.error}'));
                }
                final data = snap.data!;
                return Padding(
                  padding: const EdgeInsets.all(12),
                  child: SfCartesianChart(
                    title: ChartTitle(text: 'Market Mood Trend (${_selectedDays} days)'),
                    primaryXAxis: DateTimeAxis(
                      dateFormat: DateFormat.MMMd(),
                      intervalType: DateTimeIntervalType.days,
                      majorGridLines: MajorGridLines(width: 0.5),
                      edgeLabelPlacement: EdgeLabelPlacement.shift,
                      labelStyle: TextStyle(fontSize: 12, color: Colors.grey[700]),
                    ),
                    primaryYAxis: NumericAxis(
                      minimum: -1,
                      maximum: 1,
                      numberFormat: NumberFormat.decimalPercentPattern(decimalDigits: 0),
                      axisLine: AxisLine(width: 0),
                      majorTickLines: MajorTickLines(size: 0),
                      majorGridLines: MajorGridLines(width: 0.5),
                      labelStyle: TextStyle(fontSize: 12, color: Colors.grey[700]),
                    ),
                    plotAreaBorderWidth: 0,
                    margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    tooltipBehavior: TooltipBehavior(
                      enable: true,
                      header: '',
                      format: 'point.x : point.y',
                      textStyle: TextStyle(fontSize: 12, color: Colors.white),
                    ),
                    series: <LineSeries<HistoryPoint, DateTime>>[
                      LineSeries<HistoryPoint, DateTime>(
                        dataSource: data,
                        xValueMapper: (p, _) => p.date,
                        yValueMapper: (p, _) => p.mood,
                        width: 2,
                        color: Theme.of(context).primaryColor,
                        markerSettings: MarkerSettings(
                          isVisible: true,
                          shape: DataMarkerType.circle,
                          width: 6,
                          height: 6,
                          borderColor: Colors.white,
                          borderWidth: 1.5,
                          color: Theme.of(context).primaryColor,
                        ),
                        enableTooltip: true,
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class HistoryPoint {
  final DateTime date;
  final double mood;
  HistoryPoint({required this.date, required this.mood});
}
