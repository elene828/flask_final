import requests
import io
import csv
from datetime import datetime, timedelta
from extensions import db
from models.transaction import Transaction
from models.currency_cache import CurrencyCache

class TransactionService:
    def get_monthly_summary(self, user_id, month, year):
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.deleted_at == None,
            db.func.strftime('%m', Transaction.date) == f"{month:02d}",
            db.func.strftime('%Y', Transaction.date) == str(year)
        ).all()

        total_income = sum(t.amount for t in transactions if t.type == 'income')
        total_expense = sum(t.amount for t in transactions if t.type == 'expense')
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": total_income - total_expense
        }

    def get_category_totals(self, user_id, start_date, end_date):
        query = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.deleted_at == None,
            Transaction.type == 'expense'
        )
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        transactions = query.all()
        
        category_totals = {}
        for t in transactions:
            category_totals[t.category.name] = category_totals.get(t.category.name, 0) + t.amount
            
        return category_totals

    def export_csv(self, transactions) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['თარიღი', 'ტიპი', 'კატეგორია', 'თანხა', 'აღწერა'])
        
        for tx in transactions:
            writer.writerow([tx.date, tx.type, tx.category.name, tx.amount, tx.description])
            
        return output.getvalue()


class CurrencyConverter (TransactionService): 
    API_URL = "https://api.exchangerate-api.com/v4/latest/GEL"

    def get_rates(self) -> dict:
        cache = CurrencyCache.query.filter_by(base_currency="GEL").first()
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        if cache and cache.updated_at > one_hour_ago:
            return cache.rates_json

        try:
            response = requests.get(self.API_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                
                if rates:
                    if cache:
                        cache.rates_json = rates
                        cache.updated_at = datetime.utcnow()
                    else:
                        new_cache = CurrencyCache(base_currency="GEL", rates_json=rates, updated_at=datetime.utcnow())
                        db.session.add(new_cache)
                    
                    db.session.commit()
                    return rates
        except Exception as e:
            print(f"API Error: {e}, ანგარიშობს ძველი ქეშით.")
            
        if cache:
            return cache.rates_json
            
        return {"GEL": 1.0, "USD": 0.37, "EUR": 0.34, "GBP": 0.29} # Fallback

    def convert(self, amount, from_cur, to_cur) -> float:
        if not amount:
            return 0.0
            
        if from_cur == to_cur:
            return float(amount)
            
        rates = self.get_rates()
        
        if from_cur == "GEL":
            return round(amount * rates.get(to_cur, 1.0), 2)
            
        amount_in_gel = amount / rates.get(from_cur, 1.0) if rates.get(from_cur) else amount
        
        return round(amount_in_gel * rates.get(to_cur, 1.0), 2)