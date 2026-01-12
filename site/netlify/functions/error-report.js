// Lightweight error collection endpoint
// Errors are stored in Netlify's function logs for review

exports.handler = async (event) => {
  // Only accept POST
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  try {
    const error = JSON.parse(event.body);

    // Log to Netlify function logs (viewable in dashboard)
    console.log('[ERROR_REPORT]', JSON.stringify({
      timestamp: new Date().toISOString(),
      message: error.message,
      stack: error.stack,
      url: error.url,
      userAgent: error.userAgent,
      chapter: error.chapter,
      type: error.type
    }));

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ received: true })
    };
  } catch (e) {
    console.log('[ERROR_REPORT_PARSE_FAIL]', event.body);
    return {
      statusCode: 400,
      body: 'Invalid JSON'
    };
  }
};
