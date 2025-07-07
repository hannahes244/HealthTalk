const emergencyKeywords = [
  'chest pain', 'heart attack', 'stroke', 'seizure', 'unconscious', 
  'bleeding heavily', 'overdose', 'suicide', 'can\'t breathe', 'choking'
];

const symptomKeywords = {
  fever: ['fever', 'temperature', 'hot', 'chills'],
  headache: ['headache', 'head pain', 'migraine'],
  cough: ['cough', 'coughing', 'throat'],
  stomach: ['stomach', 'nausea', 'vomit', 'digestive'],
  pain: ['pain', 'hurt', 'ache', 'sore']
};

const responses = {
  greeting: [
    "Hello! I'm MedAssist, your AI medical companion. How can I help you today?",
    "Hi there! I'm here to provide general health information and guidance. What's on your mind?",
    "Welcome to MedAssist! I can help answer general health questions. How are you feeling?"
  ],
  emergency: [
    "⚠️ This sounds like a medical emergency. Please call emergency services (911) immediately or go to the nearest emergency room. Don't delay seeking professional medical help.",
    "🚨 URGENT: Please seek immediate medical attention by calling 911 or visiting your nearest emergency room. This requires professional medical care right away."
  ],
  fever: [
    "Fever can be a sign that your body is fighting an infection. Stay hydrated, rest, and consider over-the-counter fever reducers if appropriate. If fever persists above 103°F (39.4°C) or you have concerning symptoms, consult a healthcare provider.",
    "A fever indicates your immune system is active. Monitor your temperature, rest well, and drink plenty of fluids. Seek medical attention if fever is very high or accompanied by severe symptoms."
  ],
  headache: [
    "Headaches can have various causes including stress, dehydration, or tension. Try resting in a quiet, dark room, staying hydrated, and gentle neck stretches. If headaches are severe, frequent, or unusual for you, consult a healthcare provider.",
    "For headache relief, consider rest, hydration, and stress management. Over-the-counter pain relievers may help if appropriate. Persistent or severe headaches warrant medical evaluation."
  ],
  general: [
    "I understand your concern. While I can provide general health information, it's important to consult with a healthcare professional for personalized medical advice and proper diagnosis.",
    "Thank you for sharing that with me. For specific medical concerns, I recommend discussing this with your healthcare provider who can properly evaluate your situation.",
    "I appreciate you reaching out. Remember that while I can offer general guidance, a qualified healthcare professional can provide the most appropriate care for your specific needs."
  ],
  disclaimer: "Please remember that I'm an AI assistant providing general health information only. This is not a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers for medical concerns."
};

/**
 * Generate a medical response based on user input
 * @param {string} userMessage - The user's message
 * @returns {MedicalResponse} The generated response
 */
export function generateResponse(userMessage) {
  const message = userMessage.toLowerCase();
  
  // Check for emergency keywords
  if (emergencyKeywords.some(keyword => message.includes(keyword))) {
    return {
      response: responses.emergency[Math.floor(Math.random() * responses.emergency.length)],
      type: 'emergency'
    };
  }
  
  // Check for greeting
  if (message.includes('hello') || message.includes('hi') || message.includes('hey')) {
    return {
      response: responses.greeting[Math.floor(Math.random() * responses.greeting.length)],
      type: 'general',
      followUp: ["What symptoms are you experiencing?", "Do you have any specific health concerns?", "How can I assist with your health questions today?"]
    };
  }
  
  // Check for specific symptoms
  if (symptomKeywords.fever.some(keyword => message.includes(keyword))) {
    return {
      response: responses.fever[Math.floor(Math.random() * responses.fever.length)],
      type: 'symptom',
      followUp: ["How long have you had the fever?", "Have you taken your temperature?", "Are there any other symptoms?"]
    };
  }
  
  if (symptomKeywords.headache.some(keyword => message.includes(keyword))) {
    return {
      response: responses.headache[Math.floor(Math.random() * responses.headache.length)],
      type: 'symptom',
      followUp: ["When did the headache start?", "On a scale of 1-10, how severe is the pain?", "Have you tried any remedies?"]
    };
  }
  
  // Default response
  return {
    response: responses.general[Math.floor(Math.random() * responses.general.length)],
    type: 'advice',
    followUp: ["Can you describe your symptoms in more detail?", "When did this concern start?", "Have you experienced this before?"]
  };
}

/**
 * Generate follow-up questions based on response type
 * @param {string} type - The response type
 * @returns {string[]} Array of follow-up questions
 */
export function generateFollowUpQuestions(type) {
  const followUps = {
    general: [
      "How long have you been experiencing this?",
      "Are there any other symptoms?",
      "What brings you relief?"
    ],
    symptom: [
      "When did this start?",
      "How severe would you rate it?",
      "Have you tried anything for relief?"
    ]
  };
  
  return followUps[type] || followUps.general;
}