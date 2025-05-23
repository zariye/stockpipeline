from snow import Snowflake
import pandas as pd
import logging

class Recommend:
    def __init__(self):
        self.snow = Snowflake()
        logging.basicConfig(level=logging.INFO)

    def get(self, days=3):
        logging.info("Getting recommendations...")
        conn = self.snow.connect()
        cs = conn.cursor()

        cs.execute("SHOW TABLES IN SCHEMA STOCKDATA.PUBLIC")
        ticker_tables = [row[1] for row in cs.fetchall()]
        logging.info(f"Found {len(ticker_tables)} tables: {ticker_tables}")

        recommendations = []

        for ticker in ticker_tables:
            safe_ticker = f'"PUBLIC"."{ticker}"' if '.' in ticker else f'"PUBLIC".{ticker}'

            cs.execute(f"""
                SELECT Date, Close, Signal_Strength 
                FROM {safe_ticker}
                ORDER BY Date DESC
                LIMIT {days}
            """)

            results = cs.fetchall()
            if results:
                latest_date, latest_close, latest_signal = results[0]

                if latest_signal >= 2:
                    status = "BUY"
                elif latest_signal <= -2:
                    status = "SELL"
                else:
                    status = "HOLD"

                recommendations.append({
                    'ticker': ticker,
                    'date': latest_date,
                    'price': latest_close,
                    'signal': latest_signal,
                    'status': status
                })

        cs.close()
        conn.close()

        return pd.DataFrame(recommendations)

    def show(self):
        try:
            df = self.get()

            if df.empty:
                logging.info("No recommendations available.")
                return

            df['abs_signal'] = df['signal'].abs()
            df = df.sort_values(by=['abs_signal', 'ticker'], ascending=[False, True])
            df = df.drop(columns=['abs_signal'])

            logging.info("\n--- STOCK RECOMMENDATIONS ---\n")
            for _, row in df.iterrows():
                logging.info(f"{row['ticker']}: {row['status']} (Signal: {row['signal']}) - ${row['price']:.2f} on {row['date']}")

        except Exception as e:
            logging.error(f"Error retrieving recommendations: {str(e)}")


if __name__ == "__main__":
    recommendation = Recommend()
    recommendation.show()
