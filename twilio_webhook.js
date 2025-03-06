// This is a deployable twilio function to run the GitHub action anytime
// a text is received

exports.handler = function(context, event, callback) {
  const axios = require('axios');

  // Get GitHub configuration from environment variables
  const githubToken = context.GITHUB_TOKEN;
  const repoOwner = context.GITHUB_REPO_OWNER;
  const repoName = context.GITHUB_REPO_NAME;
  const workflowId = context.GITHUB_WORKFLOW_ID;

  // Configure GitHub API request
  const url = `https://api.github.com/repos/${repoOwner}/${repoName}/actions/workflows/${workflowId}/dispatches`;

  const data = {
    ref: 'main', // or your default branch
  };

  const headers = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': `token ${githubToken}`,
    'Content-Type': 'application/json'
  };

  // Call GitHub API to trigger workflow
  axios.post(url, data, { headers })
    .then(() => {
      console.log('Successfully triggered GitHub workflow');
      callback(null, ''); // Return empty response, don't send SMS reply
    })
    .catch(error => {
      console.error('Error triggering GitHub workflow:', error);
      callback(error);
    });
};
