package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strconv"

	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/budgets"
	"github.com/aws/aws-sdk-go/service/organizations"
	"github.com/aws/aws-sdk-go/service/sns"
)

func handler(ctx context.Context) {
	// AWSセッションを作成a
	sess := session.Must(session.NewSession())

	// AWS Organizationsのクライアントを生成
	org := organizations.New(sess)

	// AWS Organizationsの全アカウントを取得
	accounts, err := org.ListAccounts(&organizations.ListAccountsInput{})
	if err != nil {
		log.Fatalf("Failed to list accounts: %v", err)
	}

	// AWS Budgetsのクライアントを生成
	budgetsClient := budgets.New(sess)

	// 予算の基準を取得
	budgetLimit := 50000.0

	// SNSクライアントを生成
	snsClient := sns.New(sess)

	for _, account := range accounts.Accounts {
		// アカウントの予算を取得
		budget, err := budgetsClient.DescribeBudget(&budgets.DescribeBudgetInput{
			AccountId:  aws.String(*account.Id),
			BudgetName: aws.String("MonthlyBudget"),
		})
		if err != nil {
			log.Printf("Failed to describe budget for account %s: %v", *account.Id, err)
			continue
		}
		if budget.Budget.BudgetLimit != nil && budget.Budget.BudgetLimit.Amount != nil {
			amountStr := *budget.Budget.BudgetLimit.Amount
			amount, err := strconv.ParseFloat(amountStr, 64)
			if err != nil {
				log.Printf("Failed to parse budget amount for account %s: %v", *account.Id, err)
				continue
			}

			// 予算の基準を超えた場合は通知する
			if amount > budgetLimit {
				sendNotification(snsClient, *account.Id, "Budget Exceeded", "The budget of account "+*account.Id+" has exceeded the limit")
			} else if amount/2 > budgetLimit {
				sendNotification(snsClient, *account.Id, "Budget Exceeded", "The budget of account "+*account.Id+" has exceeded half of the limit")
			} else {
				log.Printf("No budget limit set for account %s", *account.Id)
			}

		}
	}
}

func sendNotification(snsClient *sns.SNS, accountId, subject, message string) {
	_, err := snsClient.Publish(&sns.PublishInput{
		TopicArn: aws.String(os.Getenv("SNS_TOPIC_ARN")),
		Message:  aws.String(message),
		Subject:  aws.String(subject),
	})
	if err != nil {
		log.Printf("Failed to send notification for account %s: %v", accountId, err)
	} else {
		fmt.Printf("Notification sent for account %s: %s\n", accountId, message)
	}
}

func main() {
	lambda.Start(handler)
}
