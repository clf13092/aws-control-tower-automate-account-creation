# コメント追加するで2222
# AWS Organizations内の全アカウントの請求情報を取得し、特定の基準を超えていたら通知する。
# 通知先はSNSトピックを指定する。
# 基準は毎月の予算の半分を超えた場合と予算を超えた場合に通知する。
# 予算はAWS Budgetsで設定する。
# 予算は各アカウント毎に毎月5万円とする。
import boto3
import os

def lambda_handler(event, context):
    # AWS Organizationsのクライアントを生成
    org = boto3.client('organizations')
    # AWS Organizationsの全アカウントを取得
    accounts = org.list_accounts()
    # AWS Budgetsのクライアントを生成
    budgets = boto3.client('budgets')
    # 予算の基準を取得
    # FIX: 予算の基準はbudgetから取得する
    budget_limit = 50000
    # 予算の基準を超えた場合に通知するSNSトピックを取得
    ses = boto3.client('ses')
    # 予算の基準を超えた場合に通知する
    # FIX: アカウントの使用量を取得する処理が必要。
    for account in accounts['Accounts']:
        # アカウントの予算を取得
        budget = budgets.describe_budget(
            AccountId=account['Id'],
            BudgetName='MonthlyBudget'
        )
        # 予算の基準を超えた場合は通知する（ここではSESを使う）

        if budget['Budget']['BudgetLimit'] > budget_limit:
            ses.send_email(
            Source='sugimori@sugichori.com',
            Destination={
                'ToAddresses': ['ryusugi777@gmail.com']
            },
            Message={
                'Subject': {
                'Data': 'Budget Exceeded'
                },
                'Body': {
                'Text': {
                    'Data': 'The budget of account ' + account['Id'] + ' has exceeded the limit'
                }
                }
            }
            )
        # 予算の半分を超えた場合は通知する（ここでもSESを使う）
        elif budget['Budget']['BudgetLimit'] / 2 > budget_limit:
            ses.send_email(
            Source='sugimori@sugichori.com',
            Destination={
                'ToAddresses': ['ryusugi777@gmail.com']
            },
            Message={
                'Subject': {
                'Data': 'Budget Exceeded'
                },
                'Body': {
                'Text': {
                    'Data': 'The budget of account ' + account['Id'] + ' has exceeded half of the limit'
                }
                }
            }
            )