// Test Google Gemini API
const GOOGLE_API_KEY = "AIzaSyDcWeUpk-I_UtWeIV4Rs8YmJSROYN8ygIk";
const MODEL_NAME = "gemini-2.0-flash-exp";

async function testApi() {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL_NAME}:generateContent?key=${GOOGLE_API_KEY}`;

    const body = {
        contents: [
            {
                role: "user",
                parts: [{ text: "Say hello in one word" }],
            },
        ],
    };

    console.log("Testing API...");

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        const data = await response.json();
        console.log("Response status:", response.status);
        console.log("Response:", JSON.stringify(data, null, 2));
    } catch (error) {
        console.error("Error:", error);
    }
}

testApi();
