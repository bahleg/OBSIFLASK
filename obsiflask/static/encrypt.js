async function decodeMeld(encodedBase64) {
    let password = prompt('enter password');
    const ITERATIONS = 210000;
    const VECTOR_SIZE = 16;
    const SALT_SIZE = 16;
    const TAG_SIZE = 16;
    try {
        // === 1. base64 → bytes ===
        const encryptedBytes = Uint8Array.from(atob(encodedBase64.trim()), c => c.charCodeAt(0));
        if (encryptedBytes.length < (VECTOR_SIZE + SALT_SIZE + TAG_SIZE)) {
            throw new Error("Encrypted data is too short to be valid!");
        }

        const iv = encryptedBytes.slice(0, VECTOR_SIZE);
        const salt = encryptedBytes.slice(VECTOR_SIZE, VECTOR_SIZE + SALT_SIZE);
        const tag = encryptedBytes.slice(encryptedBytes.length - TAG_SIZE);
        const ciphertext = encryptedBytes.slice(VECTOR_SIZE + SALT_SIZE, encryptedBytes.length - TAG_SIZE);

        // console.log({iv, salt, tag, ciphertext});

        // === 4. PBKDF2 (SHA-512) ===
        const enc = new TextEncoder();
        const keyMaterial = await crypto.subtle.importKey(
            "raw",
            enc.encode(password),
            { name: "PBKDF2" },
            false,
            ["deriveKey"]
        );

        const key = await crypto.subtle.deriveKey(
            {
                name: "PBKDF2",
                salt: salt,
                iterations: ITERATIONS,
                hash: "SHA-512"
            },
            keyMaterial,
            { name: "AES-GCM", length: 256 },
            false,
            ["decrypt"]
        );

        // === 5. AES-GCM  ===
        // WebCrypto expects tag as a part of  ciphertext:
        const fullCiphertext = new Uint8Array(ciphertext.length + TAG_SIZE);
        fullCiphertext.set(ciphertext);
        fullCiphertext.set(tag, ciphertext.length);

        const decrypted = await crypto.subtle.decrypt(
            { name: "AES-GCM", iv: iv },
            key,
            fullCiphertext
        );
        alert(new TextDecoder().decode(decrypted))
    }
    catch (err) {
        alert('error:' + err.message)
    }
}