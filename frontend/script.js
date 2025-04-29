// Initialize the API Gateway client
// If you require an API key, pass `{ apiKey: 'YOUR_API_KEY' }` as the second argument.
const apigClient = apigClientFactory.newClient({
    invokeUrl: 'https://pj93ofe9m6.execute-api.us-east-1.amazonaws.com/photos_v2',
    defaultContentType: '',
    defaultAcceptType: 'application/json' 
});
  
  //
  // Search
  //
  document.getElementById('search-btn').addEventListener('click', async () => {
    const q = document.getElementById('search-input').value.trim();
    const resDiv = document.getElementById('results');
    resDiv.innerHTML = 'Loading…';
  
    if (!q) {
      resDiv.innerHTML = '<p>Please enter a search term.</p>';
      return;
    }
  
    try {
      // apigClient.searchGet(params, body, additionalParams)
      const params = { q };
      const body = {};                  // GET has no body
      const additionalParams = {};      // no extra headers
      const response = await apigClient.searchGet(params, body, additionalParams);
      const results = response.data.results;
  
      if (!results.length) {
        resDiv.innerHTML = '<p>No results found.</p>';
        return;
      }
  
      // Render cards
      resDiv.innerHTML = '';
      results.forEach(({ url, labels }) => {
        const card = document.createElement('div');
        card.className = 'photo-card';
        card.innerHTML = `
          <img src="${url}" alt="${labels.join(', ')}"/>
          <p>${labels.join(', ')}</p>
        `;
        resDiv.appendChild(card);
      });
    } catch (err) {
      console.error('Search error:', err);
      resDiv.innerHTML = `<p style="color:red">Error: ${err.message || err.statusText}</p>`;
    }
  });
  
  //
  // Upload
  //
  document.getElementById('upload-btn').addEventListener('click', async () => {
    const fileInput    = document.getElementById('file-input');
    const labelsInput  = document.getElementById('labels-input').value.trim();
    const key          = document.getElementById('key-input').value.trim();
    const statusDiv    = document.getElementById('upload-status');
  
    statusDiv.textContent = '';
    if (!fileInput.files.length || !key) {
      statusDiv.style.color = 'red';
      statusDiv.textContent = 'Select a file and specify a filename.';
      return;
    }
  
    const file = fileInput.files[0];

    console.log(file)
    console.log(file.type)

    try {
      // apigClient.uploadPut(params, body, additionalParams)
      const params_old = { object: key };
      const additionalParams_old = {
        headers: {
          'Content-Type': file.type || 'application/octet-stream',
          'x-amz-meta-customLabels': labelsInput
        }
      };

      const params = {
        object: key,
        'Content-Type': file.type || 'application/octet-stream',
        'x-amz-meta-customLabels': labelsInput
      };
      const additionalParams = {};

  
      // The SDK will handle sending the binary body
      await apigClient.uploadPut(params, file, additionalParams);
  
      statusDiv.style.color = 'green';
      statusDiv.textContent = 'Upload successful!';
    } catch (err) {
      console.error('Upload error:', err);
      statusDiv.style.color = 'red';
      statusDiv.textContent = `Upload failed: ${err.message || err.statusText}`;
    }
  });
  