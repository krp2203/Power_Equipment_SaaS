"use client";

import { useEffect, useState } from 'react';

export default function PartSmartFrame() {
    const [token, setToken] = useState<string | null>(null);

    useEffect(() => {
        // Fetch ARI Token (Relative path)
        fetch('/api/v1/ari/token')
            .then(res => res.json())
            .then(data => setToken(data.token))
            .catch(err => console.error("Failed to load ARI token", err));

        // Listen for Add to Cart
        const handler = (event: MessageEvent) => {
            // Verify origin if possible
            if (event.data && event.data.action === 'addToCart') {
                console.log("Added to cart:", event.data.item);
                alert(`Added ${event.data.item.partNumber} to cart!`);
            }
        };
        window.addEventListener('message', handler);
        return () => window.removeEventListener('message', handler);
    }, []);

    if (!token) return <div>Loading Parts Catalog...</div>;

    // Mock HTML content
    const htmlContent = `
    <html>
      <body style="margin:0; padding: 20px; font-family: sans-serif;">
        <h1>PartSmart Catalog (Mock)</h1>
        <p>Token: ${token}</p>
        <hr/>
        <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 10px;">
            <h3>Stihl Chainsaw Chain</h3>
            <p>Part #: 3610-000-0050</p>
            <button onclick="window.parent.postMessage({action: 'addToCart', item: {partNumber: '3610-000-0050', price: 29.99}}, '*')">Add to Cart</button>
        </div>
      </body>
    </html>
  `;

    return (
        <div className="w-full h-[800px] border border-gray-300 rounded shadow bg-white">
            <iframe
                srcDoc={htmlContent}
                className="w-full h-full"
                title="PartSmart Catalog"
            />
        </div>
    );
}
