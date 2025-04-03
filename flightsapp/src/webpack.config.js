module.exports = {
    resolve: {
      fallback: {
        "https": require.resolve("https-browserify"),
        "stream": require.resolve("stream-browserify")
      }
    }
  };
  