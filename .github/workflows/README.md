# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated deployment and CI/CD processes.

## Deploy API to Fly.io

The `deploy-api.yml` workflow automatically deploys the API application to Fly.io when changes are pushed to the main branch.

### Trigger Conditions

The workflow is triggered when:

- Code is pushed to the `main` branch
- Changes are made to any of the following paths:
  - `apps/api/**` - API application code
  - `libs/core/**` - Core library changes
  - `apps/api/fly.toml` - Fly.io configuration
  - `apps/api/Dockerfile` - Docker configuration
  - `apps/api/.dockerignore` - Docker ignore rules

The workflow can also be manually triggered using the "workflow_dispatch" event.

### Required Secrets

To use this workflow, you need to set up the following repository secrets:

1. **FLY_API_TOKEN**: Your Fly.io API token
   - Generate this token in your Fly.io dashboard
   - Go to Account Settings > Access Tokens
   - Create a new token with appropriate permissions

### Setup Instructions

1. **Install Fly.io CLI locally** (for initial setup):

   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to Fly.io**:

   ```bash
   flyctl auth login
   ```

3. **Set up the API token**:
   - Go to your GitHub repository settings
   - Navigate to Secrets and variables > Actions
   - Add a new repository secret named `FLY_API_TOKEN`
   - Set the value to your Fly.io API token

4. **Verify your Fly.io app configuration**:
   - Ensure `apps/api/fly.toml` is properly configured
   - Verify the app name and region settings
   - Check that the Dockerfile path is correct

### Workflow Steps

1. **Checkout code**: Clones the repository with full history
2. **Setup Fly.io CLI**: Installs the Fly.io command-line tool
3. **Verify configuration**: Validates the Fly.io configuration file
4. **Deploy**: Builds and deploys the application to Fly.io
5. **Verify deployment**: Checks the deployment status
6. **Health check**: Performs a health check on the deployed application

### Troubleshooting

- **Deployment failures**: Check the Fly.io logs using `flyctl logs`
- **Health check failures**: Verify the application is properly configured to serve on port 8080
- **Authentication issues**: Ensure the `FLY_API_TOKEN` secret is correctly set
- **Build failures**: Check that the Dockerfile and dependencies are properly configured

### Manual Deployment

To manually trigger a deployment:

1. Go to the Actions tab in your GitHub repository
2. Select the "Deploy API to Fly.io" workflow
3. Click "Run workflow"
4. Select the branch to deploy from (defaults to main)

### Monitoring

After deployment, you can monitor your application using:

- Fly.io dashboard: [https://fly.io/apps/mss-demo-api](https://fly.io/apps/mss-demo-api)
- Application logs: `flyctl logs -a mss-demo-api`
- Application status: `flyctl status -a mss-demo-api`
