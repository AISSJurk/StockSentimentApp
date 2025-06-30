import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:syncfusion_flutter_charts/charts.dart';
import 'package:intl/intl.dart';

class StockDetailPage extends StatefulWidget {
  final String symbol;
  const StockDetailPage({required this.symbol, super.key});

  @override
  State<StockDetailPage> createState() => _StockDetailPageState();
}

class _StockDetailPageState extends State<StockDetailPage> {
  late Future<List<HistoryPoint>> _futureHistory;
  int _days = 7;

  @override
  void initState() {
    super.initState();
    _futureHistory = _fetchHistory(widget.symbol, _days);
  }

  Future<List<HistoryPoint>> _fetchHistory(String symbol, int days) async {
    final uri = Uri.parse('http://127.0.0.1:8000/history/$symbol?days=$days');
    final res = await http.get(uri);
    if (res.statusCode != 200) {
      throw Exception('Failed to load history: ${res.statusCode}');
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
        title: Text("${widget.symbol} History"),
      ),
      body: FutureBuilder<List<HistoryPoint>>(
        future: _futureHistory,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('Error: ${snap.error}'));
          }
          final data = snap.data!;

          return Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: [
                ToggleButtons(
                  isSelected: [
                    _days == 7,
                    _days == 14,
                    _days == 30,
                  ],
                  onPressed: (i) {
                    setState(() {
                      _days = [7, 14, 30][i];
                      _futureHistory = _fetchHistory(widget.symbol, _days);
                    });
                  },
                  children: const [
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Text('7d'),
                    ),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Text('14d'),
                    ),
                    Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Text('30d'),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Expanded(
                  child: SfCartesianChart(
                    title: ChartTitle(text: '${widget.symbol} Mood Trend ($_days days)'),
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
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class HistoryPoint {
  final DateTime date;
  final double mood;
  HistoryPoint({required this.date, required this.mood});
}
