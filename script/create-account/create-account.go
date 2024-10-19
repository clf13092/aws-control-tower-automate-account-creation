package main

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/budgets"
	"github.com/aws/aws-sdk-go/service/servicecatalog"
	"github.com/aws/aws-sdk-go/service/sns"
)

func createBudget(accountID string) {
	sess := session.Must(session.NewSession())
	budgetsClient := budgets.New(sess)

	budgetLimit := os.Getenv("BUDGET_LIMIT")
	snsTopic := os.Getenv("SNS_TOPIC")

	_, err := budgetsClient.CreateBudget(&budgets.CreateBudgetInput{
		AccountId: aws.String(accountID),
		Budget: &budgets.Budget{
			BudgetName: aws.String("MonthlyBudget"),
			BudgetLimit: &budgets.Spend{
				Amount: aws.Float64(budgetLimit),
				Unit:   aws.String("USD"),
			},
			BudgetType: aws.String("COST"),
			TimeUnit:   aws.String("MONTHLY"),
			TimePeriod: &budgets.TimePeriod{
				Start: aws.String("2000-01-01"),
				End:   aws.String("2099-12-31"),
			},
			CalculatedSpend: &budgets.CalculatedSpend{
				ActualSpend: &budgets.Spend{
					Amount: aws.Float64(0),
					Unit:   aws.String("USD"),
				},
			},
			CostFilters: map[string][]*string{
				"LinkedAccount": {aws.String(accountID)},
			},
			CostTypes: &budgets.CostTypes{
				IncludeTax:          aws.Bool(true),
				IncludeSubscription: aws.Bool(true),
				UseBlended:          aws.Bool(true),
			},
			NotificationsWithSubscribers: []*budgets.NotificationWithSubscribers{
				{
					Notification: &budgets.Notification{
						NotificationType:   aws.String("ACTUAL"),
						ComparisonOperator: aws.String("GREATER_THAN"),
						Threshold:          aws.Float64(100),
						ThresholdType:      aws.String("PERCENTAGE"),
						NotificationState:  aws.String("ALARM"),
					},
					Subscribers: []*budgets.Subscriber{
						{
							SubscriptionType: aws.String("SNS"),
							Address:          aws.String(snsTopic),
						},
					},
				},
			},
		},
	})

	if err != nil {
		fmt.Println("Error creating budget:", err)
		return
	}

	snsClient := sns.New(sess)
	_, err = snsClient.Publish(&sns.PublishInput{
		TopicArn: aws.String(snsTopic),
		Message:  aws.String("The budget of account " + accountID + " has exceeded the limit"),
	})

	if err != nil {
		fmt.Println("Error publishing SNS message:", err)
		return
	}

	_, err = snsClient.Publish(&sns.PublishInput{
		TopicArn: aws.String(snsTopic),
		Message:  aws.String("The budget of account " + accountID + " has exceeded half of the limit"),
	})

	if err != nil {
		fmt.Println("Error publishing SNS message:", err)
		return
	}
}

func lambdaHandler(ctx context.Context, event map[string]interface{}) {
	productID := os.Getenv("PRODUCT_ID")
	provisioningArtifactID := os.Getenv("PROVISIONING_ARTIFACT_ID")
	managedOrganizationalUnit := os.Getenv("MANAGED_ORGANIZATIONAL_UNIT")

	record := event["Records"].([]interface{})[0].(map[string]interface{})
	dynamodb := record["dynamodb"].(map[string]interface{})
	newImage := dynamodb["NewImage"].(map[string]interface{})
	email := newImage["email"].(map[string]interface{})["S"].(string)

	fmt.Println(email)

	emailWithoutDomain := strings.Split(email, "@")[0]
	firstName := newImage["first_name"].(map[string]interface{})["S"].(string)
	lastName := newImage["last_name"].(map[string]interface{})["S"].(string)

	sess := session.Must(session.NewSession())
	serviceCatalogClient := servicecatalog.New(sess)

	fmt.Println(serviceCatalogClient.ListProvisioningArtifacts(&servicecatalog.ListProvisioningArtifactsInput{
		ProductId: aws.String(productID),
	}))

	_, err := serviceCatalogClient.ProvisionProduct(&servicecatalog.ProvisionProductInput{
		ProductId:              aws.String(productID),
		ProvisioningArtifactId: aws.String(provisioningArtifactID),
		ProvisionedProductName: aws.String(emailWithoutDomain),
		ProvisioningParameters: []*servicecatalog.ProvisioningParameter{
			{
				Key:   aws.String("AccountEmail"),
				Value: aws.String(email),
			},
			{
				Key:   aws.String("AccountName"),
				Value: aws.String(emailWithoutDomain),
			},
			{
				Key:   aws.String("ManagedOrganizationalUnit"),
				Value: aws.String(managedOrganizationalUnit),
			},
			{
				Key:   aws.String("SSOUserEmail"),
				Value: aws.String(email),
			},
			{
				Key:   aws.String("SSOUserFirstName"),
				Value: aws.String(firstName),
			},
			{
				Key:   aws.String("SSOUserLastName"),
				Value: aws.String(lastName),
			},
		},
	})

	if err != nil {
		fmt.Println("Error provisioning product:", err)
		return
	}
}

func main() {
	lambda.Start(lambdaHandler)
}
