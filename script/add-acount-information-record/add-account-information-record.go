package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "os"

    "github.com/aws/aws-lambda-go/events"
    "github.com/aws/aws-lambda-go/lambda"
    "github.com/aws/aws-sdk-go/aws"
    "github.com/aws/aws-sdk-go/aws/session"
    "github.com/aws/aws-sdk-go/service/dynamodb"
    "github.com/aws/aws-sdk-go/service/dynamodb/dynamodbattribute"
)

type Event struct {
    Email           string `json:"email"`
    FirstName       string `json:"first_name"`
    LastName        string `json:"last_name"`
    RegistrationDate string `json:"registration_date"`
}

func handler(request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
    var event Event
    err := json.Unmarshal([]byte(request.Body), &event)
    if err != nil {
        return events.APIGatewayProxyResponse{
            StatusCode: http.StatusBadRequest,
            Body:       err.Error(),
        }, nil
    }

    sess := session.Must(session.NewSession())
    svc := dynamodb.New(sess)
    tableName := os.Getenv("TABLE_NAME")

    // Check if the email already exists
    result, err := svc.GetItem(&dynamodb.GetItemInput{
        TableName: aws.String(tableName),
        Key: map[string]*dynamodb.AttributeValue{
            "email": {
                S: aws.String(event.Email),
            },
        },
    })
    if err != nil {
        return events.APIGatewayProxyResponse{
            StatusCode: http.StatusInternalServerError,
            Body:       err.Error(),
        }, nil
    }

    if result.Item != nil {
        return events.APIGatewayProxyResponse{
            StatusCode: http.StatusBadRequest,
            Body:       "Account information already exists",
        }, nil
    }

    // Add the new record
    item, err := dynamodbattribute.MarshalMap(event)
    if err != nil {
        return events.APIGatewayProxyResponse{
            StatusCode: http.StatusInternalServerError,
            Body:       err.Error(),
        }, nil
    }

    _, err = svc.PutItem(&dynamodb.PutItemInput{
        TableName: aws.String(tableName),
        Item:      item,
    })
    if err != nil {
        return events.APIGatewayProxyResponse{
            StatusCode: http.StatusInternalServerError,
            Body:       err.Error(),
        }, nil
    }

    return events.APIGatewayProxyResponse{
        StatusCode: http.StatusOK,
        Body:       "Account information added successfully",
    }, nil
}

func main() {
    lambda.Start(handler)
}