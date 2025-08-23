# Indian Stock Market Backtesting System

A comprehensive Python-based backtesting system for Indian stock markets that fetches data from NSE/BSE, stores it in PostgreSQL, and implements moving average crossover strategies.

## Features

- **Data Fetching**: Fetches daily OHLCV data from NSE/BSE using NSEpy and Yahoo Finance APIs
- **Database Management**: PostgreSQL database with proper schema and indexing
- **ETL Pipeline**: Automated data extraction, transformation, and loading
- **Backtesting Engine**: Moving Average Crossover strategy implementation
- **Performance Metrics**: Returns, drawdown, Sharpe ratio, and win rate calculations
- **Visualization**: Interactive charts using Plotly and Matplotlib

## Project Structure

```
backtesting/
├── config/
│   ├── __init__.py
│   ├── database.py
│   └── settings.py
├── database/
│   ├── __init__.py
│   ├── models.py
│   ├── connection.py
│   └── operations.py
├── data/
│   ├── __init__.py
│   ├── fetcher.py
│   └── etl.py
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py
│   └── moving_average_crossover.py
├── backtesting/
│   ├── __init__.py
│   ├── engine.py
│   └── metrics.py
├── visualization/
│   ├── __init__.py
│   └── charts.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
├── requirements.txt
├── .env.example
├── main.py
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- PostgreSQL database server
- Git

### 2. Environment Setup

1. **Clone or create the project directory**
   ```bash
   cd backtesting
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv backtest_env
   # On Windows
   backtest_env\Scripts\activate
   # On macOS/Linux
   source backtest_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Database Setup

1. **Install PostgreSQL** (if not already installed)
   - Download from: https://www.postgresql.org/download/
   - Create a database user and database

2. **Configure environment variables**
   
   **Option A: Use the setup script (Recommended)**
   ```bash
   python setup_database.py
   ```
   This will guide you through creating the `.env` file with proper database credentials.
   
   **Option B: Manual configuration**
   Create a `.env` file in the project root with the following content:
   ```
   # Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=stock_backtesting
   DB_USER=your_username
   DB_PASSWORD=your_password
   
   # API Configuration
   NSEPY_TIMEOUT=30
   YAHOO_TIMEOUT=30
   
   # Default Settings
   DEFAULT_START_DATE=2020-01-01
   DEFAULT_END_DATE=2023-12-31
   DEFAULT_SHORT_WINDOW=20
   DEFAULT_LONG_WINDOW=50
   
   # Logging Configuration
   LOG_LEVEL=INFO
   LOG_FILE=backtesting.log
   ```

### 4. Database Initialization

The setup script will automatically initialize the database. If you need to do it manually:

```bash
python -c "from database.operations import init_database; init_database()"
```

### 5. Data Fetching

```bash
python -c "from data.etl import run_etl; run_etl()"
```

### 6. Complete Workflow: Real Data ETL and Backtesting

#### **Step 1: Database Setup (One-time)**
```bash
# Run the database setup script
python setup_database.py
```
This will guide you through creating the `.env` file with database credentials, test the connection, and initialize database tables.

#### **Step 2: Verify Database Connection**
```bash
# Test database operations
python test_database_fix.py
```

#### **Step 3: Test Data Fetchers**
```bash
# Verify data fetching mechanisms work
python test_fixes.py
```

#### **Step 4: Run ETL Pipeline (Fetch Real Data)**

**Option A: Incremental Update (Recommended for daily use)**
```bash
# Fetch only new data since last update (most efficient)
python etl_manager.py update

# Or using Python directly
python -c "from data.etl import run_daily_update; run_daily_update()"
```

**Option B: Full Data Fetch (Initial setup or specific date range)**
```bash
# Fetch all data for default symbols
python -c "from data.etl import run_etl; run_etl(incremental=False)"

# Fetch data for specific symbols
python -c "from data.etl import run_etl; run_etl(symbols=['RELIANCE', 'TCS', 'INFY'], incremental=False)"

# Fetch data with custom date range
python -c "from data.etl import run_etl; run_etl(symbols=['RELIANCE', 'TCS'], start_date='2022-01-01', end_date='2023-12-31', incremental=False)"
```

**Option C: Check ETL Status**
```bash
# Check which symbols need updates
python etl_manager.py status

# Check database statistics
python etl_manager.py stats
```

#### **Step 5: Verify Data in Database**
```bash
# Check that data was loaded correctly
python -c "
from database.operations import get_stock_count, get_price_count
print(f'Stocks in database: {get_stock_count()}')
print(f'Price records in database: {get_price_count()}')
print(f'Price records for RELIANCE: {get_price_count(\"RELIANCE\")}')
"
```

#### **Step 6: Run Backtesting with Real Data**
```bash
# Option A: Run backtest for a single symbol
python -c "
from backtesting.engine import backtest_engine
from strategies.moving_average_crossover import MovingAverageCrossover

strategy = MovingAverageCrossover(short_window=20, long_window=50)
results = backtest_engine.run_backtest(
    symbol='RELIANCE',
    strategy=strategy,
    start_date='2022-01-01',
    end_date='2023-12-31',
    initial_capital=100000
)

if results:
    print(f'Backtest completed for {results[\"symbol\"]}')
    print(f'Final Capital: ₹{results[\"final_capital\"]:,.2f}')
    print(f'Total Return: {results[\"metrics\"][\"total_return\"]:.2%}')
    print(f'Sharpe Ratio: {results[\"metrics\"][\"sharpe_ratio\"]:.3f}')
else:
    print('Backtest failed')
"
```

#### **Step 7: Run Full System (Recommended)**
```bash
# Run the complete workflow with real data
python main.py
```

#### **Step 8: View Results and Visualizations**
```bash
# List generated files
ls -la charts/
ls -la reports/
```

### 7. Demo Options (For Testing)

**Option A: Simple demo with mock data (Recommended for testing)**
```bash
python demo_simple.py
```

**Option B: Minimal demo without database (Best for testing)**
```bash
python demo_minimal.py
```

**Option C: Demo mode**
```bash
python main.py --demo
```

## Usage

### Basic Usage

1. **Fetch stock data**:
   ```python
   from data.etl import run_etl
   run_etl(symbols=['RELIANCE', 'TCS', 'INFY'])
   ```

2. **Run backtesting**:
   ```python
   from backtesting.engine import BacktestEngine
   from strategies.moving_average_crossover import MovingAverageCrossover
   
   engine = BacktestEngine()
   strategy = MovingAverageCrossover(short_window=20, long_window=50)
   results = engine.run_backtest('RELIANCE', strategy, '2020-01-01', '2023-12-31')
   ```

3. **Generate visualizations**:
   ```python
   from visualization.charts import plot_equity_curve, plot_signals
   plot_equity_curve(results)
   plot_signals(results)
   ```

### Advanced Usage Examples

#### **Multiple Symbols Backtesting:**
```python
from backtesting.engine import backtest_engine
from strategies.moving_average_crossover import MovingAverageCrossover

strategy = MovingAverageCrossover(short_window=20, long_window=50)
symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC']

results = backtest_engine.run_multiple_backtests(
    symbols=symbols,
    strategy=strategy,
    start_date='2022-01-01',
    end_date='2023-12-31'
)

print(f'Completed backtests for {len(symbols)} symbols')
print(f'Aggregate return: {results["aggregate_results"]["total_return"]:.2%}')
```

#### **Different Strategy Parameters:**
```python
from backtesting.engine import backtest_engine
from strategies.moving_average_crossover import MovingAverageCrossover

# Test different MA periods
strategy1 = MovingAverageCrossover(short_window=10, long_window=30)
strategy2 = MovingAverageCrossover(short_window=20, long_window=50)
strategy3 = MovingAverageCrossover(short_window=50, long_window=200)

strategies = [strategy1, strategy2, strategy3]
symbol = 'RELIANCE'

for i, strategy in enumerate(strategies, 1):
    results = backtest_engine.run_backtest(
        symbol=symbol,
        strategy=strategy,
        start_date='2022-01-01',
        end_date='2023-12-31',
        initial_capital=100000
    )
    if results:
        print(f'Strategy {i}: Return = {results["metrics"]["total_return"]:.2%}')
```

#### **Command Line Examples:**
```bash
# Multiple symbols backtesting
python -c "
from backtesting.engine import backtest_engine
from strategies.moving_average_crossover import MovingAverageCrossover

strategy = MovingAverageCrossover(short_window=20, long_window=50)
symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC']

results = backtest_engine.run_multiple_backtests(
    symbols=symbols,
    strategy=strategy,
    start_date='2022-01-01',
    end_date='2023-12-31'
)

print(f'Completed backtests for {len(symbols)} symbols')
print(f'Aggregate return: {results[\"aggregate_results\"][\"total_return\"]:.2%}')
"

# Different strategy parameters
python -c "
from backtesting.engine import backtest_engine
from strategies.moving_average_crossover import MovingAverageCrossover

strategy1 = MovingAverageCrossover(short_window=10, long_window=30)
strategy2 = MovingAverageCrossover(short_window=20, long_window=50)
strategy3 = MovingAverageCrossover(short_window=50, long_window=200)

strategies = [strategy1, strategy2, strategy3]
symbol = 'RELIANCE'

for i, strategy in enumerate(strategies, 1):
    results = backtest_engine.run_backtest(
        symbol=symbol,
        strategy=strategy,
        start_date='2022-01-01',
        end_date='2023-12-31',
        initial_capital=100000
    )
    if results:
        print(f'Strategy {i}: Return = {results[\"metrics\"][\"total_return\"]:.2%}')
"
```

### Configuration

Edit `config/settings.py` to modify:
- Default stock symbols
- Date ranges
- Strategy parameters
- Database settings

## Strategy Details

### Moving Average Crossover Strategy

- **Buy Signal**: Short-term MA crosses above long-term MA
- **Sell Signal**: Short-term MA crosses below long-term MA
- **Default Parameters**: 20-day and 50-day moving averages

## Performance Metrics

The system calculates:
- **Total Return**: Overall percentage gain/loss
- **Annualized Return**: Yearly return rate
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss

## ETL Timeline and Scheduling

### **ETL Process Timeline**

The enhanced ETL system now supports **incremental data fetching**, which means:

#### **Initial Setup (One-time)**
- **First Run**: Fetches historical data from `DEFAULT_START_DATE` to today
- **Time**: 5-10 minutes for 5 symbols (depending on data availability)
- **Data**: Complete historical OHLCV data

#### **Daily Updates (Recommended)**
- **Frequency**: Daily (after market hours)
- **Time**: 1-2 minutes for 5 symbols
- **Data**: Only new data since last fetch
- **Efficiency**: 90%+ faster than full fetch

#### **Weekly/Monthly Updates**
- **Frequency**: Weekly or monthly for maintenance
- **Time**: 2-5 minutes for 5 symbols
- **Data**: Incremental updates for any missing data

### **Recommended ETL Schedule**

#### **Daily Schedule (Production)**
```bash
# Run daily after market hours (6:00 PM IST)
python etl_manager.py update

# Check status
python etl_manager.py status
```

#### **Weekly Schedule (Maintenance)**
```bash
# Weekly full status check
python etl_manager.py status

# Clean up old data (optional)
python -c "from database.operations import cleanup_old_data; cleanup_old_data(365)"
```

#### **Monthly Schedule (Health Check)**
```bash
# Full database statistics
python etl_manager.py stats

# Verify data integrity
python -c "from data.etl import get_etl_status; print(get_etl_status())"
```

### **Automated Scheduling**

#### **Windows Task Scheduler**
```batch
# Create a batch file: daily_update.bat
@echo off
cd /d "C:\path\to\backtesting"
python etl_manager.py update --quiet
```

#### **Linux/Mac Cron Job**
```bash
# Add to crontab (daily at 6:00 PM)
0 18 * * * cd /path/to/backtesting && python etl_manager.py update --quiet
```

#### **Python Script Scheduler**
```python
import schedule
import time
from data.etl import run_daily_update

# Schedule daily update at 6:00 PM
schedule.every().day.at("18:00").do(run_daily_update)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### **ETL Performance Metrics**

| Scenario | Time | Data Size | Efficiency |
|----------|------|-----------|------------|
| Initial Setup | 5-10 min | Full historical | N/A |
| Daily Update | 1-2 min | New data only | 90%+ |
| Weekly Update | 2-5 min | Missing data | 80%+ |
| Full Refresh | 5-10 min | All data | 0% |

## Expected Outputs
```
Database setup completed successfully!
✓ Database connection test passed
✓ Database tables created
✓ Database indexes created
```

### **ETL Pipeline (Incremental Update):**
```
Running Incremental ETL Update
========================================
Symbols: RELIANCE, TCS, INFY, HDFC, ICICIBANK
Mode: Incremental (only new data)

Processing ETL for RELIANCE
Incremental fetch for RELIANCE: fetching from 2023-12-20 to 2023-12-21
Successfully processed ETL for RELIANCE (1 new records)

Processing ETL for TCS
Incremental fetch for TCS: fetching from 2023-12-20 to 2023-12-21
Successfully processed ETL for TCS (1 new records)

...

Update Results:
----------------------------------------
RELIANCE      ✓ Success
TCS           ✓ Success
INFY          ✓ Success
HDFC          ✓ Success
ICICIBANK     ✓ Success

Summary: 5/5 successful
```

### **ETL Status Check:**
```
ETL Status Report
============================================================
Report Date: 2023-12-21
Total Symbols: 5

Summary:
  ✓ Up to date: 5
  ⚠ Needs update: 0

Detailed Status:
------------------------------------------------------------
Symbol       Last Date     Days Ago   Status    
------------------------------------------------------------
RELIANCE     2023-12-21    0          ✓         
TCS          2023-12-21    0          ✓         
INFY         2023-12-21    0          ✓         
HDFC         2023-12-21    0          ✓         
ICICIBANK    2023-12-21    0          ✓         
------------------------------------------------------------
```

### **Backtesting Results:**
```
Backtest completed for RELIANCE
Final Capital: ₹125,450.00
Total Return: 25.45%
Sharpe Ratio: 1.234
Maximum Drawdown: -8.67%
Win Rate: 65.2%
```

### **Generated Files:**
- `charts/equity_curve_RELIANCE.png` - Equity curve visualization
- `charts/signals_RELIANCE.png` - Buy/sell signals chart
- `reports/backtest_report_RELIANCE.txt` - Detailed performance report

## Data Sources

- **NSEpy**: Primary source for NSE data
- **Yahoo Finance**: Backup source for international stocks
- **Manual CSV**: Support for custom data files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors like `could not translate host name "7531@localhost"`:

1. **Check your .env file**: Ensure the database configuration is correct
2. **Run the setup script**: `python setup_database.py`
3. **Verify PostgreSQL is running**: Check if PostgreSQL service is active
4. **Test connection manually**: Try connecting with `psql` command
5. **Check firewall settings**: Ensure port 5432 is not blocked

### Common Issues

- **Port number errors**: Make sure DB_PORT is a valid number (1-65535)
- **Authentication failed**: Verify username and password in .env file
- **Database doesn't exist**: Create the database manually or use the setup script
- **Permission denied**: Ensure the database user has proper permissions
- **NSEpy FrameLocalsProxy error**: This is a known bug in NSEpy. The system now includes fallback mechanisms and alternative data sources to handle this issue automatically.

### Data Fetching Issues

If you encounter issues with data fetching:

1. **Test the data fetchers**: Run `python test_fixes.py` to verify both fetchers work
2. **Use alternative fetcher**: The system automatically falls back to Yahoo Finance if NSEpy fails
3. **Check internet connection**: Ensure you have stable internet access
4. **Try different symbols**: Some symbols might not be available on all sources

#### **Troubleshooting Commands:**
```bash
# Test data fetchers
python test_fixes.py

# Try with different symbols
python -c "from data.etl import run_etl; run_etl(symbols=['RELIANCE'])"

# Check if data exists for a symbol
python -c "
from database.operations import get_price_count
print(f'RELIANCE records: {get_price_count(\"RELIANCE\")}')
"
```

### Monitoring and Maintenance

#### **Check System Performance:**
```bash
# View logs
tail -f backtesting.log

# Check database size
python -c "
from database.operations import get_stock_count, get_price_count
print(f'Database contains {get_stock_count()} stocks and {get_price_count()} price records')
"
```

#### **Clean Up Old Data:**
```bash
# Remove data older than 1 year
python -c "from database.operations import cleanup_old_data; cleanup_old_data(365)"
```

### Quick Start Summary

For a quick test of the complete workflow:

```bash
# 1. Setup database
python setup_database.py

# 2. Test everything works
python test_database_fix.py
python test_fixes.py

# 3. Fetch real data (incremental)
python etl_manager.py update

# 4. Check ETL status
python etl_manager.py status

# 5. Run backtesting
python main.py

# 6. View results
ls -la charts/
```

### Daily Usage Workflow

For regular daily usage:

```bash
# Daily update (after market hours)
python etl_manager.py update

# Check status
python etl_manager.py status

# Run backtesting with latest data
python main.py
```

### Getting Help

If you continue to have issues:
1. Check the logs in `backtesting.log`
2. Verify your PostgreSQL installation
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

## Disclaimer

This software is for educational and research purposes only. Past performance does not guarantee future results. Always do your own research before making investment decisions.
