import datetime
import os
import uuid

from flask import Flask, request
import models
from models import User, Transac, Review, Deposit, Currency, Account
import database
import sqlalchemy
from celery_worker import task1


app = Flask(__name__)
date_now = datetime.datetime.now().strftime("%d-%m-%Y")










# homepage
@app.route("/")
def Homepage():
    return "<p>Hello! This is the homepage</p>"


@app.route('/currency/list', methods=['GET'])#Works
def Currency_List():
    database.init_db()
    result = Currency.query.all()
    return [itm.to_dict() for itm in result]


# 2page
@app.route('/currency/<currency_name>', methods=['GET'])#Works
def currency_info(currency_name):
    database.init_db()
    res = Currency.query.filter_by(CurrencyName=currency_name)
    return [itm.to_dict() for itm in res]


# 3page
@app.get('/currency/trade/<currency_name1>X<currency_name2>')#Works
def trade_pair(currency_name1, currency_name2):
    database.init_db()
    res = round((Currency.query.filter_by(CurrencyName=currency_name1,
                                               Date=date_now).first().NameToUSDPrice) / (
                     Currency.query.filter_by(CurrencyName=currency_name2,
                                              Date=date_now).first().NameToUSDPrice), 2)
    return f"The cost of {currency_name1} to {currency_name2} : {res}"


# 5page
@app.route('/users', methods=['GET'])#works
def get_users():
    database.init_db()
    result = User.query.all()
    return [itm.to_dict() for itm in result]


@app.route('/currency/<currency_name>/rating', methods = ['GET', 'POST'])#works
def add_currency_rating(currency_name):
    database.init_db()
    if request.method == 'POST':
        request_data = request.get_json()
        rating = request_data['Rating']
        comment = request_data['Comment']
        rating_piece = Review(CurrencyName=currency_name, Rating=rating, Comment=comment)
        database.db_session.add(rating_piece)
        database.db_session.commit()
        return "ok!"
    else:
        all_ratings = Review.query.all()
        currency_rating = dict(
            database.db_session.query(
                sqlalchemy.func.avg(models.Review.Rating).label('rate')
            ).filter(
                models.Review.CurrencyName == currency_name
            ).first()
        )['rate']
        rate_history = [itm.to_dict() for itm in all_ratings]
        return {"Rate_History": rate_history, "average": currency_rating, "currency_name": currency_name}


@app.post('/currency/trade/<currency_name1>x<currency_name2>')#Works
def exchange(currency_name1, currency_name2):
    request_data = request.get_json()
    user_id = request_data['user_id']
    amount1 = request_data['amount']
    OperType = request_data['OperType']
    fee = request_data['fee']



    transaction_id = str(uuid.uuid4())
    database.init_db()
    transaction_queue_record = models.TransactionQueue(transaction_id=str(transaction_id), status="in queue")
    database.db_session.add(transaction_queue_record)
    database.db_session.commit()

    transaction_record = models.TransactionQueue.query.filter_by(transaction_id=str(transaction_id)).first()
    print(transaction_record)

    task_obj = task1.apply_async(args=[user_id, currency_name1, currency_name2, amount1, OperType, fee, transaction_id])
    return {'task id': str(task_obj)}





if __name__ == '__main__':
    app.run(host='0.0.0.0')
