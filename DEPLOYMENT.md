# Runner Deployment Overview

## AWS Deployment 1

### Target Architecture
1. VPC
    - 2 Public & 2 private subnets for 
        - high availability
        - Required by Load balancer & ECS
        - LEast privilege
    - Public Subnets (Internet-Facing)
        - Only Load balancers & NAT here
            - ALB - Incoming 
                - layer 7 (HTTP/HTTPS)
                - used by clients on internet
            - NAT - Outgoing
                - layer 3
                - allow outbound to internet
                - block inbound from internet
                - ECS to Strava API
                    - but not strava to ECS
                - used by private servers/services
                - private subnets have no public IPS need NAT
    - Private Subnets (App-Facing)
        - ECS
        - DB
2. ECS Fargate (Container native)
    - Service 1 -> Runner Backend (FastAPI)
    - Service 2 -> Runner Frontend (nginx + React)
3. Application Load Balancer - ALB 
    - public/internet facing
    - Accept incoming internet traffic
    - Forward to backend services
    - layer 7 - HTTP/HTTPS
    - listens on :80 or :443
    - targets frontend ECS
        - proxy to backend internally
            - or expose backend on seperate port
4. RDS -> PostgreSQL
    - Small instance - db.t4g.micro
    - private subnet
    - security group allows traffic only from backend ECS tasks
5. ECR
    - runner-backend repo
    - runner frontend repo
6. secrets / config
    - SSM parameter store or Secret manager
    - DATABASE_URL
    - STRAVA ACCESS TOKEN
    - Other API keys
7. Observability 
    - ECS task logs -> cloud watch logs
    - ALB access logs -> optional S3 bucket


If you ever want a ultra-cheap version, we can also do:
	•	Single EC2 t3.micro running your docker-compose with an ALB in front

2. GitHub Actions pipeline: what we’ll eventually have

Workflow A: Infra pipeline (Terraform)

Goal:
On pushes to main (or via manual dispatch), run:
	1.	terraform fmt, terraform validate
	2.	terraform plan
	3.	Optional: require manual approval
	4.	terraform apply (for main only)

Key points to show in interview:
	•	GitHub → AWS via OIDC (no long-lived AWS keys)
	•	Separate “plan” vs “apply”
	•	Remote state in S3 with DynamoDB state locking

⸻

Workflow B: App build & deploy

Goal:
	1.	On push to main:
	•	Build backend & frontend Docker images
	•	Tag with git SHA (and maybe latest)
	•	Push to ECR
	2.	Trigger deploy:
	•	Either:
	•	Terraform re-apply with new image tags (image tag variables), or
	•	A lighter “update ECS service” job that:
	•	Registers a new task definition with new image tags
	•	Updates ECS service to use new revision

Bonus interview points:
	•	Cache Docker layers
	•	Run tests before building images
	•	Maybe run a simple security scan (e.g. Trivy) on images
	•	Notifications on failure (GitHub Checks + later Slack/email)

⸻

3. What you should do right now (concrete next steps)

Let’s start with Terraform infra skeleton, since CI/CD depends on it.

Step 1: Create infra/ directory and basic Terraform config

In your repo root, create:

infra/main.tf: