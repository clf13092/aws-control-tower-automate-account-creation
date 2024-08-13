# 社員のメールアドレスと名前と登録日付をjson形式のeventという変数で受取り、DynamoDBにレコードとして登録するLambda関数
# このLambda関数は、API GatewayのPOSTメソッドで呼び出されることを想定している
# このLambda関数は、DynamoDBのテーブルにレコードを追加し、アカウント作成のためのLambda関数を呼び出す
import boto3
import json

def lambda_handler(event, context);
    # event変数には、API GatewayのPOSTメソッドで受け取ったjson形式のリクエストが格納されている
    # event変数の中身は以下のようになっている
    # {
    #   "email": "メールアドレス",
    #   "name": "名前",
    #   "registration_date": "登録日付"
    # }
    # この情報をDynamoDBに登録する
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('account-information')
    # メールアドレスがすでに登録されているかどうかをチェックする
    response = table.get_item(
        Key={
            'email': event['email']
        }
    )
    if 'Item' in response:
        return {
            'statusCode': 400,
            'body': json.dumps('Account information already exists')
        }
    # メールアドレスが登録されていない場合は、DynamoDBにレコードを追加する
    else:
        table.put_item(
            Item={
                'email': event['email'],
                'name': event['name'],
                'registration_date': event['registration_date']
            }
        )
        return {
            'statusCode': 200,
            'body': json.dumps('Account information added successfully')
        }


    