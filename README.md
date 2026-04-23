# Creator Cloud Studio

Creator Cloud Studio is a hybrid cloud application for event poster submissions. Users submit a title, a short description, and a real poster image file. The system stores the submission, runs background validation, and returns one final result: `READY`, `NEEDS REVISION`, or `INCOMPLETE`.

## Tech Stack

- Amazon EC2 with Docker containers
- Amazon S3 for event and file storage
- AWS Lambda for background processing
- Amazon DynamoDB for submission state
- Flask for the three service APIs

## Services

- `presentation-service`: front end and result polling
- `workflow-service`: submission handling and S3 upload
- `data-service`: submission state read/write

## Validation Rules

1. Missing required fields -> `INCOMPLETE`
2. Description shorter than 30 characters -> `NEEDS REVISION`
3. Invalid poster filename extension -> `NEEDS REVISION`
4. Otherwise -> `READY`

Accepted extensions: `.jpg`, `.jpeg`, `.png`

## Structure

```text
creator-cloud-studio/
├── data-service/
├── lambda/
│   ├── processing-function/
│   ├── result-update-function/
│   └── submission-event-function/
├── presentation-service/
└── workflow-service/
```

## Deployment

The web interface is served from:

```text
http://<EC2-PUBLIC-IP>:5000/
```

Service ports:

- `presentation-service`: `5000`
- `data-service`: `5001`
- `workflow-service`: `5002`
