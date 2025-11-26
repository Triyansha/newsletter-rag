import { useState } from 'react';

export default function NewsletterRAGPreview() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Welcome! I\'m ready to help you explore your newsletters. Try asking about topics, trends, or specific content from your synced newsletters.' }
  ]);
  const [input, setInput] = useState('');
  
  const sampleNewsletters = [
    { title: 'Tech Weekly #42', sender: 'tech@digest.com', date: '2024-01-15' },
    { title: 'AI Insights', sender: 'ai@newsletter.io', date: '2024-01-14' },
    { title: 'Morning Brew', sender: 'crew@morningbrew.com', date: '2024-01-13' },
  ];

  const handleSend = () => {
    if (!input.trim()) return;
    
    setMessages(prev => [
      ...prev,
      { role: 'user', content: input },
      { role: 'assistant', content: `Based on your newsletters, I found some relevant insights about "${input}". Several of your subscribed newsletters have discussed this topic recently, including Tech Weekly and AI Insights. Would you like me to provide more specific details from any particular newsletter?` }
    ]);
    setInput('');
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #2c1810 0%, #1a0f0a 100%)',
      fontFamily: 'Georgia, serif',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        {/* Leather Header */}
        <div style={{
          background: 'linear-gradient(180deg, #5c4033 0%, #3d2914 100%)',
          borderRadius: '16px 16px 0 0',
          padding: '28px 32px',
          border: '4px solid #2a1a0f',
          borderBottom: 'none',
          boxShadow: 'inset 0 2px 4px rgba(255,255,255,0.1), inset 0 -2px 4px rgba(0,0,0,0.3), 0 4px 20px rgba(0,0,0,0.5)',
          position: 'relative'
        }}>
          {/* Stitching */}
          <div style={{
            position: 'absolute',
            top: '10px',
            left: '24px',
            right: '24px',
            height: '2px',
            background: 'repeating-linear-gradient(90deg, transparent, transparent 10px, #8b7355 10px, #8b7355 20px)',
            opacity: 0.4
          }} />
          
          <h1 style={{
            color: '#c9a227',
            fontSize: '2.5rem',
            fontWeight: 600,
            margin: 0,
            textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
            letterSpacing: '2px'
          }}>
            📬 Newsletter RAG
          </h1>
          <p style={{
            color: '#d4c4a8',
            fontSize: '1.1rem',
            marginTop: '8px',
            fontStyle: 'italic'
          }}>
            Your personal newsletter knowledge base
          </p>
        </div>

        {/* Main Content Area */}
        <div style={{ display: 'flex', gap: 0 }}>
          {/* Sidebar */}
          <div style={{
            width: '240px',
            background: 'linear-gradient(90deg, #2c1810 0%, #3d2914 100%)',
            borderLeft: '4px solid #2a1a0f',
            borderBottom: '4px solid #2a1a0f',
            borderRadius: '0 0 0 16px',
            padding: '20px',
            position: 'relative'
          }}>
            {/* Spine decoration */}
            <div style={{
              position: 'absolute',
              top: 0,
              right: 0,
              width: '12px',
              height: '100%',
              background: 'linear-gradient(90deg, #2a1a0f 0%, #4a3020 50%, #2a1a0f 100%)',
              boxShadow: 'inset -2px 0 4px rgba(0,0,0,0.3)'
            }} />
            
            <h3 style={{ color: '#c9a227', fontSize: '1.1rem', marginTop: 0, marginBottom: '16px' }}>
              📚 Library
            </h3>
            
            {/* Stats */}
            <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
              <div style={{
                background: 'linear-gradient(135deg, #3d2914 0%, #2c1810 100%)',
                padding: '12px',
                borderRadius: '8px',
                border: '2px solid #5c4033',
                flex: 1,
                textAlign: 'center'
              }}>
                <div style={{ color: '#a89070', fontSize: '0.75rem' }}>Newsletters</div>
                <div style={{ color: '#c9a227', fontSize: '1.4rem', fontWeight: 600 }}>24</div>
              </div>
              <div style={{
                background: 'linear-gradient(135deg, #3d2914 0%, #2c1810 100%)',
                padding: '12px',
                borderRadius: '8px',
                border: '2px solid #5c4033',
                flex: 1,
                textAlign: 'center'
              }}>
                <div style={{ color: '#a89070', fontSize: '0.75rem' }}>Chunks</div>
                <div style={{ color: '#c9a227', fontSize: '1.4rem', fontWeight: 600 }}>156</div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid #5c4033', margin: '16px 0', opacity: 0.5 }} />
            
            <h4 style={{ color: '#c9a227', fontSize: '0.9rem', marginBottom: '12px' }}>
              📰 Recent
            </h4>
            
            {sampleNewsletters.map((nl, i) => (
              <div key={i} style={{
                background: 'linear-gradient(135deg, #fffef8 0%, #f5edd5 100%)',
                border: '2px solid #c9b896',
                borderRadius: '8px',
                padding: '10px 12px',
                marginBottom: '8px',
                boxShadow: '2px 2px 6px rgba(0,0,0,0.2)',
                cursor: 'pointer',
                transition: 'transform 0.2s'
              }}>
                <div style={{ color: '#3d2914', fontWeight: 600, fontSize: '0.85rem' }}>{nl.title}</div>
                <div style={{ color: '#5c4033', fontSize: '0.75rem' }}>{nl.sender}</div>
              </div>
            ))}
          </div>

          {/* Chat Area */}
          <div style={{
            flex: 1,
            background: 'linear-gradient(180deg, #f4e4bc 0%, #e8d5a3 100%)',
            borderRight: '4px solid #2a1a0f',
            borderBottom: '4px solid #2a1a0f',
            borderRadius: '0 0 16px 0',
            padding: '24px',
            minHeight: '400px',
            position: 'relative',
            boxShadow: 'inset 3px 0 8px rgba(0,0,0,0.1), inset -3px 0 8px rgba(0,0,0,0.1)'
          }}>
            {/* Lined paper effect */}
            <div style={{
              position: 'absolute',
              top: 0,
              left: '50px',
              width: '2px',
              height: '100%',
              background: 'rgba(180, 100, 100, 0.15)'
            }} />
            
            {/* Messages */}
            <div style={{ marginBottom: '80px' }}>
              {messages.map((msg, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: '16px'
                }}>
                  <div style={{
                    maxWidth: '70%',
                    padding: '14px 18px',
                    borderRadius: '10px',
                    fontFamily: "'Source Sans Pro', sans-serif",
                    fontSize: '0.95rem',
                    lineHeight: 1.6,
                    ...(msg.role === 'user' ? {
                      background: 'linear-gradient(135deg, #3d2914 0%, #2c1810 100%)',
                      color: '#f4e4bc',
                      border: '2px solid #5c4033',
                      boxShadow: '3px 3px 10px rgba(0,0,0,0.3)'
                    } : {
                      background: 'linear-gradient(135deg, #fffef5 0%, #f5edd5 100%)',
                      color: '#1a1a1a',
                      border: '2px solid #c9b896',
                      boxShadow: '3px 3px 10px rgba(0,0,0,0.15)'
                    })
                  }}>
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>

            {/* Input Area */}
            <div style={{
              position: 'absolute',
              bottom: '20px',
              left: '24px',
              right: '24px',
              display: 'flex',
              gap: '12px'
            }}>
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyPress={e => e.key === 'Enter' && handleSend()}
                placeholder="Ask about your newsletters..."
                style={{
                  flex: 1,
                  background: 'linear-gradient(180deg, #fffef8 0%, #f8f0dc 100%)',
                  border: '2px solid #8b7355',
                  borderRadius: '8px',
                  padding: '14px 18px',
                  fontFamily: "'Source Sans Pro', sans-serif",
                  fontSize: '1rem',
                  color: '#1a1a1a',
                  boxShadow: 'inset 2px 2px 5px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.1)',
                  outline: 'none'
                }}
              />
              <button
                onClick={handleSend}
                style={{
                  background: 'linear-gradient(180deg, #5c4033 0%, #3d2914 100%)',
                  color: '#c9a227',
                  border: '2px solid #2a1a0f',
                  borderRadius: '8px',
                  padding: '14px 28px',
                  fontFamily: "'Source Sans Pro', sans-serif",
                  fontWeight: 600,
                  fontSize: '0.95rem',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 8px rgba(0,0,0,0.3), inset 0 1px 2px rgba(255,255,255,0.1)',
                  transition: 'all 0.2s'
                }}
              >
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          background: 'linear-gradient(180deg, #3d2914 0%, #2c1810 100%)',
          borderRadius: '0 0 16px 16px',
          padding: '16px',
          border: '4px solid #2a1a0f',
          borderTop: 'none',
          textAlign: 'center',
          marginTop: '-4px'
        }}>
          <p style={{ color: '#8b7355', fontSize: '0.85rem', margin: 0 }}>
            Powered by Google Gemini & ChromaDB
          </p>
        </div>
      </div>
    </div>
  );
}
