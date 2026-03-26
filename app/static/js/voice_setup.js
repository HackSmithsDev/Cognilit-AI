/**
 * CogniLit-AI Global Voice Service
 * Handles TTS for Settings, Chat, and Curriculum Previews
 */

const PERSONA_MAP = {
    'Nova':    ['Aria', 'Ava', 'Google US English', 'Microsoft Ava', 'Samantha'],
    'Echo':    ['Andrew', 'Google UK English Male', 'Guy', 'Microsoft James', 'Microsoft David'],
    'Shimmer': ['Emma', 'Google UK English Female', 'Microsoft Soft', 'Sonia', 'Zira'],
    'Onyx':    ['Brian', 'Google US English Male', 'Microsoft David', 'Daniel', 'Arthur'],
    'Sky':     ['Jenny', 'Victoria', 'Google US English Female', 'Ana', 'Microsoft Natasha'],
    'Default': []
};

/**
 * Ensures voices are loaded before trying to speak
 */
function getBrowserVoices() {
    return new Promise((resolve) => {
        let voices = window.speechSynthesis.getVoices();
        if (voices.length !== 0) {
            resolve(voices);
        } else {
            window.speechSynthesis.onvoiceschanged = () => {
                voices = window.speechSynthesis.getVoices();
                resolve(voices);
            };
        }
    });
}

/**
 * Main Global Speak Function
 * @param {string} text - The text to be spoken
 */
async function speak(text) {
    if (!window.isAudioEnabled) return;
    
    // Stop any current speaking to prevent overlap
    window.speechSynthesis.cancel();

    const voices = await getBrowserVoices();
    const utterance = new SpeechSynthesisUtterance(text);
    
    const currentPersona = window.userVoicePreference || 'Nova';
    const currentLang = window.userLanguagePreference || 'English (US)';
    const isMalePersona = ['Echo', 'Onyx'].includes(currentPersona);

    // 1. Determine Language Code
    let langPrefix = 'en';
    if (currentLang === 'Hindi') langPrefix = 'hi';
    if (currentLang === 'Spanish') langPrefix = 'es';

    // 2. Filter voices by language
    let langVoices = voices.filter(v => v.lang.startsWith(langPrefix));
    
    // Fallback to English if the specific language pack isn't installed
    if (langVoices.length === 0) langVoices = voices.filter(v => v.lang.startsWith('en'));

    // 3. TIER 1: Match by specific name in PERSONA_MAP
    const candidates = PERSONA_MAP[currentPersona] || [];
    let selectedVoice = langVoices.find(v => 
        candidates.some(name => v.name.includes(name))
    );

    // 4. TIER 2: Strict Gender Fallback (If Tier 1 fails)
    if (!selectedVoice && currentPersona !== 'Default') {
        const maleNames = ['male', 'david', 'andrew', 'guy', 'james', 'brian', 'daniel', 'pawan'];
        const femaleNames = ['female', 'aria', 'zira', 'samantha', 'jenny', 'emma', 'susan', 'nova', 'kalpana'];

        selectedVoice = langVoices.find(v => {
            const name = v.name.toLowerCase();
            if (isMalePersona) {
                return maleNames.some(m => name.includes(m)) && !femaleNames.some(f => name.includes(f));
            } else {
                return femaleNames.some(f => name.includes(f));
            }
        });
    }

    // 5. TIER 3: Failsafe (Grab first available in that language)
    if (!selectedVoice) selectedVoice = langVoices[0];

    if (selectedVoice) {
        utterance.voice = selectedVoice;
        console.log(`🎙️ [${currentPersona} | ${currentLang}] -> ${selectedVoice.name}`);
    }

    // 6. Persona Tuning (Pitch & Rate)
    // We manually adjust these to simulate "Neural" qualities even on standard voices
    if (isMalePersona) {
        utterance.pitch = 0.85; 
        utterance.rate = 0.95; 
    } else if (currentPersona === 'Sky') {
        utterance.pitch = 1.15;
        utterance.rate = 1.05;
    } else {
        utterance.pitch = 1.0;
        utterance.rate = 1.0;
    }


    const volBtn = document.getElementById('volume-toggle-btn');
    if (volBtn) {
        utterance.onstart = () => {
            volBtn.classList.add('pulse-animation');
        };

        utterance.onend = () => {
            volBtn.classList.remove('pulse-animation');
        };

        // Handle errors or manual cancellations
        utterance.onerror = () => {
            volBtn.classList.remove('pulse-animation');
        };
    }
    window.speechSynthesis.speak(utterance);
}