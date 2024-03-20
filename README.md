# Heidi
## Multilingual Voice Bot for Streamlined Call Management
With Heidi we aim to reduce the number of calls the Kanton St. Gallen Office has to handle manually by deploying a voice bot capable of answering common questions and redirecting callers to fitting departments like the Migrationsamt. 
We accomplish that goal by utilizing Azure Communication Services for handling phone call event data along with Azure Cognitive Services for Text2Speech and Speech2Text in multiple languages and dialects including swiss german, as well as Azure AI Services for generating responses based on scraped information and phone numbers from the Kanton St. Gallen website. Utilizing Azure services, Heidi offers a FADP compliant solution to automated call processing.

## Getting Started
Heidi is a multifaceted voicebot that integrates seamlessly with Microsoft Azure's Communication Services, Cognitive Services, and OpenAI Services to provide an interactive experience to callers. Before diving into the project, familiarize yourself with the technical foundations and the role each service plays in Heidi’s system architecture.
Here are the precise steps to initiate your journey with Heidi:

**Provisioning a Phone Number**: Begin by acquiring a dedicated phone number for Heidi, which callers will use to engage with the bot. This step is crucial for establishing the initial point of contact and can be done by following Microsoft's guide to [getting a phone number](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/telephony/get-phone-number?tabs=windows&pivots=platform-azp).

**Event Handling with Azure Communication Services**: Once you have your number, Azure Communication Services will enable you to handle and respond to call events. Heidi makes use of this service to detect when there is an incoming call and initiates the interaction process. For more detail on event handling, refer to the official Microsoft documentation on [handling calling events](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/voice-video-calling/handle-calling-events).

**Engaging Callers with Text-to-Speech (TTS)**: Heidi communicates with callers by converting text to audible speech using Azure's robust [TTS services](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-text-to-speech?tabs=macos%2Cterminal&pivots=programming-language-python). This ensures that Heidi can relay information and prompts vocally to callers.

**Listening and Responding with Speech-to-Text (STT)**: To understand caller responses, Heidi incorporates Azure's [STT technologies](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-speech-to-text?tabs=macos%2Cterminal&pivots=programming-language-python) to transcribe spoken words into text effectively.

**Leveraging Azure OpenAI for Conversational AI**: To interpret caller's intents and craft coherent replies, Heidi utilizes Azure OpenAI Services. These advanced AI models allow Heidi to [process and respond](https://learn.microsoft.com/en-us/azure/ai-services/openai/chatgpt-quickstart?tabs=command-line%2Cpython-new&pivots=programming-language-python) intelligently, leading to a natural and seamless conversation flow in real time.

By following these steps and leveraging Azure’s powerful suite of services, you can bring your own voice assistant to life, following Heidi's lead in revolutionizing caller interaction within public administration.

## Deployment
When you're ready to bring Heidi to life for testing and public interaction, setting up your deployment is a critical step. We propose using Railway for initial testing due to its straightforward setup process. While Railway offers quick deployment, be mindful that it may introduce higher costs if used as a long-term solution. As your needs evolve, you may consider transitioning to a more permanent infrastructure that suits your budget and scale requirements.

### Deployment Prerequisites:
Before starting the deployment, ensure you have the following:

A Railway account for hosting your backend service.
Properly set up an instance in Railway with the necessary services ready to receive the deployment build.

### Required Environment Variables:
The environment upon which Heidi runs requires specific variables to be set. Whether deploying on Railway or other cloud services, you must define the following variables within your hosting environment:

**ACS_CONNECTION_STRING** - This is your Azure Communication Services resource connection string.

**COGNITIVE_SERVICE_ENDPOINT** - The endpoint for your Azure Cognitive Services, critical for speech-to-text and text-to-speech functionalities.

**AZURE_OPENAI_SERVICE_KEY** - Your subscription key for Azure OpenAI services used for generating chat responses. Note that this is different from the Cognitive Services key.

**AZURE_OPENAI_DEPLOYMENT_MODEL** - This variable specifies the Azure OpenAI deployment model you're utilizing, such as "gpt-4-turbo-preview" or "gpt-3.5-turbo". Choose the model that best fits your bot's complexity and conversational requirements.

**AGENT_PHONE_NUMBER** - The phone number that the voicebot will use to relay calls to a live agent if necessary. Ensure proper formatting with country code.

**CALLBACK_URI_HOST** - The base URI for your deployment on Railway, appended with the necessary path to handle callback events. This URI is critical for Azure Communication Services to communicate with your application.

### Step-by-Step Deployment
1. Access your Railway dashboard and select the relevant project for deployment.
2. Navigate to the 'Variables' section and input each of the required environment variables with their corresponding values.
3. Deploy your application by connecting Railway to your GitHub repository containing the project source code or directly through Railway's CLI deployment options.
4. Once deployed, verify the functionality by conducting test calls to ensure the voicebot is responsive and the environment variables are correctly configured.
For more detailed instructions and troubleshooting, refer to Railway’s documentation and service-specific setup guides on Microsoft Azure's documentation. Proper deployment will set a strong foundation for Heidi to function reliably, providing callers with an exceptional and helpful interaction experience.

## Cost Management and Data Privacy Considerations

Operating Heidi, the voicebot, incurs costs that fluctuate based on the specific Azure services utilized and the hosting infrastructure selected. Below, we provide a snapshot of potential expenses to help you estimate the cost of running Heidi in a standard deployment scenario:

### Estimated Service Costs:

#### Azure Communications Services Voice:
Comprehensive voice services enable the core functionality of the voicebot. Precise rates are delineated in the [pricing details](https://learn.microsoft.com/en-us/azure/communication-services/concepts/pricing).

#### Azure Cognitive Services:
These services provide essential AI capabilities for language processing. You can explore the different tiers and usage-based pricing on the [official pricing page](https://azure.microsoft.com/de-de/pricing/details/cognitive-services/speech-services/#pricing).

#### Azure OpenAI Services:
Advanced conversational AI models that underpin the voicebot’s natural and intuitive interactions, with pricing structures available on the [pricing page](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/).

#### Railway Hosting:
While ideal for quick deployment, Railway's pricing may vary based on resource consumption. For a detailed breakdown, visit [Railway's pricing structure](https://railway.app/pricing).

### Data Privacy Framework:

Heidi’s operation within a privacy-focused framework is of paramount importance. As such, consider the following guidelines to ensure compliance with data privacy standards:

Adhere to stringent data protection regulations including the General Data Protection Regulation (GDPR) and the Swiss Federal Act on Data Protection (FADP), especially when processing and storing user data.
Azure's regional services can serve as a robust option for meeting data privacy requirements. By deploying in an Azure region that complies with local data privacy laws, you can provide additional assurance to users regarding the safety and confidentiality of their personal data.
Regularly review and update your data handling practices to reflect any changes in legislation or industry best practices.
Ensuring fiscal prudence while prioritizing user privacy will contribute to the sustainable, trustworthy, and responsible operation of Heidi's voicebot services.

## Credits
Heidi was developed during the START Hack in St.Gallen as a solution to the Kanton St. Gallen Challenge which can be found [here](https://github.com/START-Hack/CantonOfStGallen_STARTHACK24).
