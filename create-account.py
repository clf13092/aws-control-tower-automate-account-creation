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

def lambda_handler(event,context):
    # service catalogからアカウント作成用のポートフォリオの情報を取得する。
    # この情報は環境変数に設定されている
    product_id = os.environ['PRODUCT_ID']
    managed_organizational_unit = os.environ['MANAGED_ORGANIZATIONAL_UNIT']
    email = event['Records'][0]['dynamodb']['NewImage']['email']['S']
    # プロビジョン後の製品の名前のために、emailから@以降を取り除いた文字列を取得する
    email_without_domain = email.split('@')[0]
    first_name = event['Records'][0]['dynamodb']['NewImage']['first_name']['S']
    last_name = event['Records'][0]['dynamodb']['NewImage']['last_name']['S']

    # service catalogのクライアントを生成する
    service_catalog = boto3.client('servicecatalog')
    # service catalogの製品からアカウントを作成する
    service_catalog.provision_product(
        ProductId=product_id,
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
