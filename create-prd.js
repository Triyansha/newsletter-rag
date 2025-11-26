const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        Header, Footer, AlignmentType, LevelFormat, HeadingLevel, 
        BorderStyle, WidthType, ShadingType, PageNumber } = require('docx');
const fs = require('fs');

// ============================================================================
// Newsletter RAG - Product Requirements Document
// ============================================================================

const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Georgia", size: 24 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal",
        run: { size: 56, bold: true, color: "1a1a2e", font: "Palatino Linotype" },
        paragraph: { spacing: { before: 0, after: 200 }, alignment: AlignmentType.CENTER } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: "16213e", font: "Palatino Linotype" },
        paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: "0f3460", font: "Palatino Linotype" },
        paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 1 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullet-list",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "num-features",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "num-milestones",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [{
    properties: {
      page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    headers: {
      default: new Header({ children: [new Paragraph({ 
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "Newsletter RAG PRD", italics: true, color: "666666", size: 20 })]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ 
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Page ", size: 20, color: "666666" }), 
          new TextRun({ children: [PageNumber.CURRENT], size: 20, color: "666666" }), 
          new TextRun({ text: " of ", size: 20, color: "666666" }), 
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 20, color: "666666" })
        ]
      })] })
    },
    children: [
      // Title
      new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("Newsletter RAG")] }),
      new Paragraph({ 
        alignment: AlignmentType.CENTER,
        spacing: { after: 400 },
        children: [new TextRun({ text: "Personal Newsletter Aggregator with AI-Powered Search", italics: true, color: "555555", size: 26 })]
      }),

      // Overview
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Overview")] }),
      new Paragraph({ 
        spacing: { after: 200 },
        children: [new TextRun("Newsletter RAG is a personal tool that connects to your Gmail, extracts newsletter content, and enables intelligent conversation with your curated knowledge base. Using retrieval-augmented generation (RAG), you can ask questions, discover connections, and resurface insights from newsletters you've accumulated over time.")]
      }),

      // Problem Statement
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Problem Statement")] }),
      new Paragraph({ 
        spacing: { after: 200 },
        children: [new TextRun("Newsletters pile up unread. Valuable insights get buried in email archives. Traditional search fails to surface relevant content across multiple sources. Users need a way to extract value from their newsletter subscriptions without manually reading each one.")]
      }),

      // Core Features
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Core Features")] }),
      new Paragraph({ numbering: { reference: "num-features", level: 0 }, children: [
        new TextRun({ text: "Gmail OAuth Integration: ", bold: true }), new TextRun("Secure connection to Gmail using OAuth 2.0 with read-only access to fetch newsletter emails.")
      ]}),
      new Paragraph({ numbering: { reference: "num-features", level: 0 }, children: [
        new TextRun({ text: "Newsletter Detection: ", bold: true }), new TextRun("Automatic identification and filtering of newsletter emails using heuristics like unsubscribe headers and sender patterns.")
      ]}),
      new Paragraph({ numbering: { reference: "num-features", level: 0 }, children: [
        new TextRun({ text: "Content Extraction: ", bold: true }), new TextRun("HTML cleaning via Trafilatura to extract readable text while preserving structure.")
      ]}),
      new Paragraph({ numbering: { reference: "num-features", level: 0 }, children: [
        new TextRun({ text: "Vector Embeddings: ", bold: true }), new TextRun("Text chunking and embedding generation using Google Gemini for semantic search capability.")
      ]}),
      new Paragraph({ numbering: { reference: "num-features", level: 0 }, children: [
        new TextRun({ text: "Conversational Interface: ", bold: true }), new TextRun("Chat with your newsletters using natural language. Ask questions, request summaries, and discover related content.")
      ]}),

      // Tech Stack
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Technical Architecture")] }),
      new Table({
        columnWidths: [3000, 6360],
        rows: [
          new TableRow({
            tableHeader: true,
            children: [
              new TableCell({ borders: cellBorders, width: { size: 3000, type: WidthType.DXA },
                shading: { fill: "1a1a2e", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "Component", bold: true, color: "FFFFFF" })] })]
              }),
              new TableCell({ borders: cellBorders, width: { size: 6360, type: WidthType.DXA },
                shading: { fill: "1a1a2e", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "Technology", bold: true, color: "FFFFFF" })] })]
              })
            ]
          }),
          new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 3000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Runtime")] })] }),
            new TableCell({ borders: cellBorders, width: { size: 6360, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Python 3.11+")] })] })
          ]}),
          new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 3000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Email API")] })] }),
            new TableCell({ borders: cellBorders, width: { size: 6360, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Gmail API (google-api-python-client)")] })] })
          ]}),
          new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 3000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("HTML Cleaning")] })] }),
            new TableCell({ borders: cellBorders, width: { size: 6360, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Trafilatura")] })] })
          ]}),
          new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 3000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Vector Database")] })] }),
            new TableCell({ borders: cellBorders, width: { size: 6360, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("ChromaDB (persistent local storage)")] })] })
          ]}),
          new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 3000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("AI Provider")] })] }),
            new TableCell({ borders: cellBorders, width: { size: 6360, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Google Gemini (embeddings + chat)")] })] })
          ]}),
          new TableRow({ children: [
            new TableCell({ borders: cellBorders, width: { size: 3000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Frontend")] })] }),
            new TableCell({ borders: cellBorders, width: { size: 6360, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Streamlit with skeuomorphic CSS")] })] })
          ]})
        ]
      }),

      // Project Structure
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Project Structure")] }),
      new Paragraph({ 
        spacing: { after: 100 },
        children: [new TextRun({ text: "newsletter-rag/", font: "Courier New", size: 22 })]
      }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "config.py", font: "Courier New" }), new TextRun(" — Environment and API configuration")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "gmail_client.py", font: "Courier New" }), new TextRun(" — OAuth flow and email fetching")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "newsletter_detector.py", font: "Courier New" }), new TextRun(" — Newsletter identification logic")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "content_cleaner.py", font: "Courier New" }), new TextRun(" — HTML extraction with Trafilatura")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "embeddings.py", font: "Courier New" }), new TextRun(" — Text chunking and Gemini embeddings")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "vector_store.py", font: "Courier New" }), new TextRun(" — ChromaDB operations")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "rag_engine.py", font: "Courier New" }), new TextRun(" — RAG query pipeline")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "app.py", font: "Courier New" }), new TextRun(" — Streamlit web interface")] }),

      // Milestones
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Development Milestones")] }),
      new Paragraph({ numbering: { reference: "num-milestones", level: 0 }, children: [
        new TextRun({ text: "Phase 1: ", bold: true }), new TextRun("Gmail integration and newsletter detection")
      ]}),
      new Paragraph({ numbering: { reference: "num-milestones", level: 0 }, children: [
        new TextRun({ text: "Phase 2: ", bold: true }), new TextRun("Content extraction and embedding pipeline")
      ]}),
      new Paragraph({ numbering: { reference: "num-milestones", level: 0 }, children: [
        new TextRun({ text: "Phase 3: ", bold: true }), new TextRun("RAG engine and chat interface")
      ]}),
      new Paragraph({ numbering: { reference: "num-milestones", level: 0 }, children: [
        new TextRun({ text: "Phase 4: ", bold: true }), new TextRun("UI polish and skeuomorphic styling")
      ]}),

      // Success Metrics
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Success Metrics")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun("Newsletter detection accuracy > 95%")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun("Query response time < 3 seconds")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun("Relevant context retrieval in top-5 results > 80%")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun("Clean content extraction without formatting artifacts")] }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/mnt/user-data/outputs/Newsletter_RAG_PRD.docx", buffer);
  console.log("PRD created successfully!");
});
