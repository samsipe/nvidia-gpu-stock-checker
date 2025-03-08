// This is a deployable twilio function to run the GitHub action anytime
// a text is received

exports.handler = function(context, event, callback) {
  const axios = require('axios');

  // Get GitHub configuration from environment variables
  const githubToken = context.GITHUB_TOKEN;
  const repoOwner = 'samsipe';
  const repoName = 'nvidia-gpu-stock-checker';
  const workflowId = 'check_stock.yml';

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
