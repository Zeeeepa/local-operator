// Constants
const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

// Utility functions
const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
};

const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// Components
const LoadingIndicator = () => (
    <div className="loading-indicator">
        <div className="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
);

const Message = ({ message }) => {
    const { role, content, timestamp } = message;
    
    // Use DOMPurify to sanitize HTML and marked to render markdown
    const renderContent = () => {
        if (!content) return '';
        const sanitizedContent = DOMPurify.sanitize(marked.parse(content));
        return { __html: sanitizedContent };
    };
    
    return (
        <div className={`message ${role}`}>
            <div className="message-header">
                {role === 'user' ? 'You' : 'Assistant'} • {formatTimestamp(timestamp)}
            </div>
            <div 
                className="message-content"
                dangerouslySetInnerHTML={renderContent()}
            />
        </div>
    );
};

const AgentItem = ({ agent, isActive, onClick }) => (
    <div 
        className={`agent-item ${isActive ? 'active' : ''}`}
        onClick={() => onClick(agent.id)}
    >
        <h3>{agent.name}</h3>
        <p>{agent.description || 'No description'}</p>
    </div>
);

const CreateAgentModal = ({ isOpen, onClose, onSubmit, models, providers }) => {
    const [formData, setFormData] = React.useState({
        name: '',
        description: '',
        hosting: 'openrouter',
        model: 'google/gemini-2.0-flash-001',
    });
    
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };
    
    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(formData);
    };
    
    if (!isOpen) return null;
    
    return (
        <div className="modal-backdrop">
            <div className="modal-content">
                <div className="modal-header">
                    <h2>Create New Agent</h2>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>
                <form className="create-agent-form" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="name">Name</label>
                        <input 
                            type="text" 
                            id="name" 
                            name="name" 
                            value={formData.name}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="description">Description</label>
                        <textarea 
                            id="description" 
                            name="description" 
                            value={formData.description}
                            onChange={handleChange}
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="hosting">Provider</label>
                        <select 
                            id="hosting" 
                            name="hosting" 
                            value={formData.hosting}
                            onChange={handleChange}
                        >
                            {providers.map(provider => (
                                <option key={provider.id} value={provider.id}>
                                    {provider.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label htmlFor="model">Model</label>
                        <select 
                            id="model" 
                            name="model" 
                            value={formData.model}
                            onChange={handleChange}
                        >
                            {models
                                .filter(model => model.provider === formData.hosting)
                                .map(model => (
                                    <option key={model.id} value={model.id}>
                                        {model.name || model.id}
                                    </option>
                                ))}
                        </select>
                    </div>
                    <div className="form-actions">
                        <button type="button" className="cancel-btn" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="submit-btn">
                            Create Agent
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// Main App Component
const App = () => {
    // State
    const [agents, setAgents] = React.useState([]);
    const [selectedAgentId, setSelectedAgentId] = React.useState(null);
    const [messages, setMessages] = React.useState([]);
    const [inputMessage, setInputMessage] = React.useState('');
    const [isLoading, setIsLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const [models, setModels] = React.useState([]);
    const [providers, setProviders] = React.useState([]);
    const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);
    const [selectedModel, setSelectedModel] = React.useState('google/gemini-2.0-flash-001');
    const [selectedProvider, setSelectedProvider] = React.useState('openrouter');
    const [websocket, setWebsocket] = React.useState(null);
    const [clientId] = React.useState(generateUUID());
    
    const chatContainerRef = React.useRef(null);
    
    // Fetch agents on component mount
    React.useEffect(() => {
        fetchAgents();
        fetchModels();
        fetchProviders();
        setupWebSocket();
        
        return () => {
            if (websocket) {
                websocket.close();
            }
        };
    }, []);
    
    // Scroll to bottom of chat when messages change
    React.useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);
    
    // Fetch conversation when agent changes
    React.useEffect(() => {
        if (selectedAgentId) {
            fetchConversation(selectedAgentId);
        } else {
            setMessages([]);
        }
    }, [selectedAgentId]);
    
    // Setup WebSocket connection
    const setupWebSocket = () => {
        const ws = new WebSocket(`${WS_BASE_URL}/ws/${clientId}`);
        
        ws.onopen = () => {
            console.log('WebSocket connection established');
            // Send ping every 30 seconds to keep connection alive
            const pingInterval = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        command: 'ping',
                        data: { timestamp: Date.now() }
                    }));
                }
            }, 30000);
            
            // Store the interval ID to clear it when the component unmounts
            ws.pingInterval = pingInterval;
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.event === 'chat_update') {
                handleChatUpdate(data);
            } else if (data.event === 'job_update') {
                handleJobUpdate(data);
            }
        };
        
        ws.onclose = () => {
            console.log('WebSocket connection closed');
            if (ws.pingInterval) {
                clearInterval(ws.pingInterval);
            }
            
            // Try to reconnect after a delay
            setTimeout(() => {
                if (document.visibilityState !== 'hidden') {
                    setupWebSocket();
                }
            }, 3000);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        setWebsocket(ws);
    };
    
    const handleChatUpdate = (data) => {
        if (data.is_complete) {
            // Final update for this message
            setMessages(prevMessages => {
                // Find if we already have a message with this ID
                const existingIndex = prevMessages.findIndex(m => m.id === data.message_id);
                
                if (existingIndex >= 0) {
                    // Update existing message
                    const updatedMessages = [...prevMessages];
                    updatedMessages[existingIndex] = {
                        ...updatedMessages[existingIndex],
                        content: data.content,
                    };
                    return updatedMessages;
                } else {
                    // Add new message
                    return [...prevMessages, {
                        id: data.message_id,
                        role: data.role,
                        content: data.content,
                        timestamp: new Date().toISOString(),
                    }];
                }
            });
            
            setIsLoading(false);
        } else {
            // Streaming update
            setMessages(prevMessages => {
                // Find if we already have a message with this ID
                const existingIndex = prevMessages.findIndex(m => m.id === data.message_id);
                
                if (existingIndex >= 0) {
                    // Update existing message
                    const updatedMessages = [...prevMessages];
                    updatedMessages[existingIndex] = {
                        ...updatedMessages[existingIndex],
                        content: data.content,
                    };
                    return updatedMessages;
                } else {
                    // Add new message
                    return [...prevMessages, {
                        id: data.message_id,
                        role: data.role,
                        content: data.content,
                        timestamp: new Date().toISOString(),
                    }];
                }
            });
        }
    };
    
    const handleJobUpdate = (data) => {
        if (data.status === 'completed' && data.result) {
            // Job completed, update messages
            setMessages(prevMessages => [
                ...prevMessages,
                {
                    id: generateUUID(),
                    role: 'assistant',
                    content: data.result.response,
                    timestamp: new Date().toISOString(),
                }
            ]);
            
            setIsLoading(false);
        } else if (data.status === 'failed' && data.error) {
            // Job failed
            setError(`Error: ${data.error}`);
            setIsLoading(false);
        }
    };
    
    // API calls
    const fetchAgents = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/v1/agents`);
            const data = await response.json();
            
            if (data.status === 200 && data.result) {
                setAgents(data.result.agents);
                
                // If there are agents and none is selected, select the first one
                if (data.result.agents.length > 0 && !selectedAgentId) {
                    setSelectedAgentId(data.result.agents[0].id);
                }
            }
        } catch (error) {
            console.error('Error fetching agents:', error);
            setError('Failed to load agents. Please try again.');
        }
    };
    
    const fetchModels = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/v1/models`);
            const data = await response.json();
            
            if (data.models) {
                setModels(data.models);
            }
        } catch (error) {
            console.error('Error fetching models:', error);
        }
    };
    
    const fetchProviders = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/v1/models/providers`);
            const data = await response.json();
            
            if (data.providers) {
                setProviders(data.providers);
            }
        } catch (error) {
            console.error('Error fetching providers:', error);
        }
    };
    
    const fetchConversation = async (agentId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/v1/agents/${agentId}/conversation`);
            const data = await response.json();
            
            if (data.status === 200 && data.result) {
                // Convert conversation records to our message format
                const formattedMessages = data.result.messages.map(msg => ({
                    id: generateUUID(),
                    role: msg.role,
                    content: msg.content,
                    timestamp: new Date().toISOString(),
                }));
                
                setMessages(formattedMessages);
            }
        } catch (error) {
            console.error('Error fetching conversation:', error);
            setError('Failed to load conversation. Please try again.');
        }
    };
    
    const createAgent = async (agentData) => {
        try {
            const response = await fetch(`${API_BASE_URL}/v1/agents`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(agentData),
            });
            
            const data = await response.json();
            
            if (data.status === 201 && data.result) {
                // Refresh agents list
                fetchAgents();
                // Close modal
                setIsCreateModalOpen(false);
                // Select the newly created agent
                setSelectedAgentId(data.result.id);
            } else {
                setError(data.message || 'Failed to create agent. Please try again.');
            }
        } catch (error) {
            console.error('Error creating agent:', error);
            setError('Failed to create agent. Please try again.');
        }
    };
    
    const sendMessage = async () => {
        if (!inputMessage.trim() || !selectedAgentId) return;
        
        // Add user message to the chat
        const userMessageId = generateUUID();
        setMessages(prev => [
            ...prev,
            {
                id: userMessageId,
                role: 'user',
                content: inputMessage,
                timestamp: new Date().toISOString(),
            }
        ]);
        
        setInputMessage('');
        setIsLoading(true);
        setError(null);
        
        try {
            // Send message to the API
            const response = await fetch(`${API_BASE_URL}/v1/chat/agents/${selectedAgentId}/async`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: inputMessage,
                    hosting: selectedProvider,
                    model: selectedModel,
                    persist_conversation: true,
                    user_message_id: userMessageId,
                }),
            });
            
            const data = await response.json();
            
            if (data.status === 202 && data.result) {
                // Subscribe to job updates via WebSocket
                if (websocket && websocket.readyState === WebSocket.OPEN) {
                    websocket.send(JSON.stringify({
                        command: 'subscribe_job',
                        data: { job_id: data.result.id }
                    }));
                }
            } else {
                setError(data.message || 'Failed to send message. Please try again.');
                setIsLoading(false);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            setError('Failed to send message. Please try again.');
            setIsLoading(false);
        }
    };
    
    // Event handlers
    const handleAgentSelect = (agentId) => {
        setSelectedAgentId(agentId);
    };
    
    const handleInputChange = (e) => {
        setInputMessage(e.target.value);
    };
    
    const handleSubmit = (e) => {
        e.preventDefault();
        sendMessage();
    };
    
    const handleCreateAgent = (formData) => {
        createAgent(formData);
    };
    
    const handleModelChange = (e) => {
        setSelectedModel(e.target.value);
    };
    
    const handleProviderChange = (e) => {
        setSelectedProvider(e.target.value);
        // Reset model selection to first model of the new provider
        const providerModels = models.filter(model => model.provider === e.target.value);
        if (providerModels.length > 0) {
            setSelectedModel(providerModels[0].id);
        }
    };
    
    // Render
    return (
        <div className="app-container">
            {/* Sidebar */}
            <div className="sidebar">
                <div className="sidebar-header">
                    <h1>Local Operator</h1>
                    <button 
                        className="new-chat-btn"
                        onClick={() => setIsCreateModalOpen(true)}
                    >
                        New Agent
                    </button>
                </div>
                <div className="agents-list">
                    {agents.map(agent => (
                        <AgentItem 
                            key={agent.id}
                            agent={agent}
                            isActive={agent.id === selectedAgentId}
                            onClick={handleAgentSelect}
                        />
                    ))}
                </div>
                <div className="sidebar-footer">
                    Local Operator v1.0.0
                </div>
            </div>
            
            {/* Main Content */}
            <div className="main-content">
                {selectedAgentId ? (
                    <>
                        {/* Chat Container */}
                        <div className="chat-container" ref={chatContainerRef}>
                            {messages.map(message => (
                                <Message key={message.id} message={message} />
                            ))}
                            {isLoading && <LoadingIndicator />}
                            {error && (
                                <div className="error-message">
                                    {error}
                                </div>
                            )}
                        </div>
                        
                        {/* Input Container */}
                        <div className="input-container">
                            <div className="model-selector">
                                <label htmlFor="provider">Provider:</label>
                                <select 
                                    id="provider" 
                                    value={selectedProvider}
                                    onChange={handleProviderChange}
                                >
                                    {providers.map(provider => (
                                        <option key={provider.id} value={provider.id}>
                                            {provider.name}
                                        </option>
                                    ))}
                                </select>
                                
                                <label htmlFor="model" style={{ marginLeft: '16px' }}>Model:</label>
                                <select 
                                    id="model" 
                                    value={selectedModel}
                                    onChange={handleModelChange}
                                >
                                    {models
                                        .filter(model => model.provider === selectedProvider)
                                        .map(model => (
                                            <option key={model.id} value={model.id}>
                                                {model.name || model.id}
                                            </option>
                                        ))}
                                </select>
                            </div>
                            
                            <form className="message-form" onSubmit={handleSubmit}>
                                <textarea
                                    className="message-input"
                                    value={inputMessage}
                                    onChange={handleInputChange}
                                    placeholder="Type your message here..."
                                    disabled={isLoading}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault();
                                            sendMessage();
                                        }
                                    }}
                                />
                                <button 
                                    type="submit" 
                                    className="send-btn"
                                    disabled={isLoading || !inputMessage.trim()}
                                >
                                    Send
                                </button>
                            </form>
                        </div>
                    </>
                ) : (
                    <div className="welcome-screen">
                        <h2>Welcome to Local Operator</h2>
                        <p>
                            Select an existing agent from the sidebar or create a new one to get started.
                            Local Operator allows you to chat with AI agents that can execute code and
                            perform tasks on your device.
                        </p>
                        <button onClick={() => setIsCreateModalOpen(true)}>
                            Create Your First Agent
                        </button>
                    </div>
                )}
            </div>
            
            {/* Create Agent Modal */}
            <CreateAgentModal 
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onSubmit={handleCreateAgent}
                models={models}
                providers={providers}
            />
        </div>
    );
};

// Render the App
ReactDOM.createRoot(document.getElementById('root')).render(<App />);