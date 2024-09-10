# アカウントをサービスカタログから作成する関数
# DynamoDB StreamによってトリガーされるLambda関数
# Lambda関数のevent変数には、DynamoDB Streamからのイベント情報が格納されている
# event変数の中身は以下のようになっている
# {
#   "Records": [
#     {
#       "eventID": "1",
#       "eventName": "INSERT",
#       "eventVersion": "1.0",
#       "eventSource": "aws:dynamodb",
#       "awsRegion": "us-west-2",
#       "dynamodb": {
#         "Keys": {
#           "email": {
#             "S": "メールアドレス"
#           }
#         },
#         "NewImage": {
#           "email": {
#             "S": "メールアドレス"
#           },
#           "first_name": {
#             "S": "名前"
#           },
#           "last_name": {
#             "S": "苗字"
#           },
#           "registration_date": {
#             "S": "登録日付"
#           }
#         },
#         "SequenceNumber": "111",
#         "SizeBytes": 26,
#         "StreamViewType": "NEW_AND_OLD_IMAGES"
#       },
#       "eventSourceARN": "eventsourcearn"
#     }
#   ]
# }
# この情報を使って、アカウントをサービスカタログに登録する
import boto3
import os

# AWS Budgetsを作成する関数
# 予算の基準を超えた場合に通知するSNSトピックを指定する
# 予算の基準は環境変数に設定されている
# 予算の基準は毎月の予算の半分を超えた場合と予算を超えた場合に通知する
# 予算はAWS Budgetsで設定する
def create_budget(account_id):
    # AWS Budgetsのクライアントを生成
    budgets = boto3.client('budgets')
    # 予算の基準を取得
    budget_limit = int(os.environ['BUDGET_LIMIT'])
    # 予算の基準を超えた場合に通知するSNSトピックを取得
    sns_topic = os.environ['SNS_TOPIC']
    # 予算を作成
    budgets.create_budget(
        AccountId=account_id,
        Budget={
            'BudgetName': 'MonthlyBudget',
            'BudgetLimit': budget_limit,
            'BudgetType': 'COST',
            'TimeUnit': 'MONTHLY',
            'TimePeriod': {
                'Start': '2000-01-01',
                'End': '2099-12-31'
            },
            'CalculatedSpend': {
                'ActualSpend': {
                    'Amount': '0',
                    'Unit': 'USD'
                }
            },
            'CostFilters': {
                'LinkedAccount': [account_id]
            },
            'CostTypes': {
                'IncludeTax': True,
                'IncludeSubscription': True,
                'UseBlended': True
            },
            'Notification': {
                'NotificationType': 'ACTUAL',
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': 100,
                'ThresholdType': 'PERCENTAGE',
                'NotificationState': 'ALARM'
            }
        }
    )
    # 予算の基準を超えた場合に通知する
    sns = boto3.client('sns')
    sns.publish(
        TopicArn=sns_topic,
        Message='The budget of account ' + account_id + ' has exceeded the limit'
    )
    # 予算の半分を超えた場合に通知する
    sns.publish(
        TopicArn=sns_topic,
        Message='The budget of account ' + account_id + ' has exceeded half of the limit'
    )

def lambda_handler(event,context):
    # service catalogからアカウント作成用のポートフォリオの情報を取得する。
    # この情報は環境変数に設定されている
    # デバッグ用にevent変数の中身を出力する
    product_id = os.environ['PRODUCT_ID']
    provisioning_artifact_id = os.environ['PROVISIONING_ARTIFACT_ID']
    managed_organizational_unit = os.environ['MANAGED_ORGANIZATIONAL_UNIT']
    email = event['Records'][0]['dynamodb']['NewImage']['email']['S']
    print(email)
    # プロビジョン後の製品の名前のために、emailから@以降を取り除いた文字列を取得する
    email_without_domain = email.split('@')[0]
    first_name = event['Records'][0]['dynamodb']['NewImage']['first_name']['S']
    last_name = event['Records'][0]['dynamodb']['NewImage']['last_name']['S']

    # service catalogのクライアントを生成する
    service_catalog = boto3.client('servicecatalog')
    # デバッグ用にservice catalogのプロダクト情報を取得
    print(service_catalog.list_provisioning_artifacts(ProductId=product_id))
    # service catalogの製品からアカウントを作成する
    service_catalog.provision_product(
        ProductId=product_id,
        ProvisioningArtifactId=provisioning_artifact_id,
        ProvisionedProductName=email_without_domain,
        ProvisioningParameters=[
            {
                'Key': 'AccountEmail',
                'Value': email
            },
            {
                'Key': 'AccountName',
                'Value': email_without_domain
            },
            {
                'Key': 'ManagedOrganizationalUnit',
                'Value': managed_organizational_unit
            },
            {
                'Key': 'SSOUserEmail',
                'Value': email
            },
            {
                'Key': 'SSOUserFirstName',
                'Value': first_name
            },
            {
                'Key': 'SSOUserLastName',
                'Value': last_name
            }
        ]
    )