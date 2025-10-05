async function decodeMeld(encodedBase64) {
    let password = prompt('enter password');
    if (!password) return alert('empty password');
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


async function encodeMeld() {
    const ITERATIONS = 210000;
    const VECTOR_SIZE = 16;
    const SALT_SIZE = 16;
    const TAG_SIZE = 16;
    let plaintext = prompt('enter text to encode');
    if (!plaintext) return alert('empty text');
    let password = prompt('enter password');
    if (!password) return alert('empty password');
    let password2 = prompt('enter password again');
    if (password != password2) return alert('passwords do not match');

    try {
        const enc = new TextEncoder();
        const data = enc.encode(plaintext);

        // iv and salt
        const iv = crypto.getRandomValues(new Uint8Array(VECTOR_SIZE));
        const salt = crypto.getRandomValues(new Uint8Array(SALT_SIZE));

        // PBKDF2(SHA-512)
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
            ["encrypt"]
        );

        // encrypt
        const encrypted = await crypto.subtle.encrypt(
            { name: "AES-GCM", iv: iv },
            key,
            data
        );

        const encryptedBytes = new Uint8Array(encrypted);


        const tag = encryptedBytes.slice(encryptedBytes.length - TAG_SIZE);
        const ciphertext = encryptedBytes.slice(0, encryptedBytes.length - TAG_SIZE);

        // IV + salt + ciphertext + tag
        const result = new Uint8Array(VECTOR_SIZE + SALT_SIZE + ciphertext.length + TAG_SIZE);
        result.set(iv, 0);
        result.set(salt, VECTOR_SIZE);
        result.set(ciphertext, VECTOR_SIZE + SALT_SIZE);
        result.set(tag, VECTOR_SIZE + SALT_SIZE + ciphertext.length);

        // into
        const base64 = btoa(String.fromCharCode(...result));
        prompt("Your encripted message:", '🔐β ' + base64 + ' 🔐');

    }
    catch (err) {
        alert('error:' + err.message)
    }
}
