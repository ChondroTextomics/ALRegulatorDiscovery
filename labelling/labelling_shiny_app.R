library(shiny)
library(shinyWidgets)
library(shinythemes)
library(shinyBS)
library(shinyalert)
library(shinyFiles)
library(fs)

# Functions ####

highlight_genes <- function(text, start_index, end_index, colour){
  text_processed <- text

  # We are going to order first the start indexes
  indexes_order <- order(start_index)
  start <- start_index[indexes_order]
  end <- end_index[indexes_order]
  
  offset <- 0 # initial
  
  before_gen_text <- paste0("<span style='background-color: ", colour,"; padding: 2px; border-radius: 3px;'>")
  after_gene_text <- "</span>"
  offset_added_text <- nchar(before_gen_text) + nchar(after_gene_text)
  
  for (gene in seq_along(start)){
    start_index <- start[gene] + offset
    end_index <- end[gene] + offset
    
    gene_text <- substring(text_processed, start_index, end_index)
    
    text_processed <- paste0(
      substring(text_processed, 1, start_index - 1),  # text before the gene
      before_gen_text,  # before HTML tag
      gene_text,  # gene text
      after_gene_text,  # after HTML tag
      substring(text_processed, end_index + 1 , nchar(text_processed))  # text after the gene
    )
    
    
    offset <- offset + offset_added_text
  }
  
  return(text_processed)
}

# Front-End ####
ui <- fluidPage(
  theme = shinytheme("paper"),
  tags$style(HTML("
    /* Ensure tab content is centered but allows scrolling */
    .tab-content {
      display: block; /* We have changed this so the content doesnt jump that much from left to right */
      justify-content: center;
      align-items: center;
      min-height: 70vh; /* Adjust so it's not too tall */
      padding-top: 50px; /* Prevents tabs from being covered */
      overflow-y: auto; /* Allows scrolling if needed */
    }
    
    /* Slightly increase font size */
    body {
      font-size: 17px; /* Default was ~16px */
    }
")),
  
  tabsetPanel( # to create tabs
    # Start Window ####
    tabPanel("Start",
             style = "background-color: #ffffff; border-radius: 12px; 
             box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.1); 
             color: #2c3e50; font-size: 18px; line-height: 1.7;",
             
             h2("Welcome to the Chondrogenesis Sentence Labeling App", 
                style = "margin-bottom: 20px; color:#2196F3;"),
             br(),
             h3("What is this?"),
             p("This app is aimed at labelling sentences related to chondrogenesis."),
             p("Your labeling work will be used to train a machine learning model 
       to distinguish between sentences that identify chondrogenesis drivers 
       and those that do not."),
             hr(style = "border: 1px solid #bdc3c7; margin: 20px 0;"),  # Grey horizontal line
             
             h3("What is your role in the app?"),
             p("You are responsible for carefully reviewing and labeling the sentences 
       presented to you. Each user has their own labeling tasks, 
       so it’s important that you identify yourself correctly before starting."),
             hr(style = "border: 1px solid #bdc3c7; margin: 20px 0;"),  # Grey horizontal line
             
             h3("Where do you find instructions?"),
             p("For detailed guidance on how to label sentences, please visit the ",
               strong("Instructions and Rules"),
               " window."),
             hr(style = "border: 1px solid #bdc3c7; margin: 20px 0;"),  # Grey horizontal line
             
             h3("How do you define who you are?"),
             p("Go to the ",
               strong("User"),
               " window to set up your user identity. This ensures you only label 
       your assigned sentences — this step is very important!"),
             hr(style = "border: 1px solid #bdc3c7; margin: 20px 0;"),  # Grey horizontal line
             
             h3("How do you start labeling?"),
             p("Once you’re ready, head over to the ",
               strong("Label"),
               " window to begin labeling sentences."),
             hr(style = "border: 1px solid #bdc3c7; margin: 20px 0;"),  # Grey horizontal line
             
             h3("Need help?"),
             p("For any doubts or questions, please send a message to ",
               a(href = "mailto:a.valdes@liverpool.ac.uk", "a.valdes@liverpool.ac.uk"),
               ".")
    ),
    
    # User Window ####
    tabPanel("User", id = "user-tab", # We add an ID so the tags are working only in this tab
             div(
               style = "max-width: 900px; margin: 0 auto; padding: 20px 0;",
               h2("Selection File to Label", style = "color:#2196F3"),
               # Create a container for centering the selectInput
               div(class = "select-input-container", 
                   #selectInput("person", "Select User",
                   #            choices = c("Ana", "Jamie", "PlaceHolder"),
                   #            selected = "PlaceHolder"),
                   shinyFilesButton("file", "Choose a file", "Select a file to label", multiple = FALSE),
                   verbatimTextOutput("chosen_file")
                 ),
               htmlOutput("fileEdited")
               )
            )
    
             ,
    # Label Window ####
    tabPanel("Label", id = "labelling-tab", #name of the tab
             h2("Sentence Labelling", style = "color:#2196F3"),
             sidebarLayout(
                 sidebarPanel(
                   class = "side-panel", # New insertion
                   width = 4,
                   
                   h3("Gene to label"),
                   htmlOutput("sentence"), # This will showcase the sentence
                   
                   # Add some space between the objects
                   tags$br(),  # Adds a single line break
                   uiOutput("dynamicButton"),  # Placeholder for the button of gene or not a gene
                   
                   tags$br(),  # Adds a single line break
                   tags$br(),  # Adds a single line break
                   
                   h3("Sentence with all the genes"),
                   htmlOutput("sentenceComplete"), # This will showcase the sentence
                   # Add some space between the objects
                   tags$br(),  # Adds a single line break
                   actionButton("moreGenes", "More genes"),
                   uiOutput("dynamic_ui"), # This will appear if we push more genes
                   # New in v2, we are adding the no drivers in sentence
                   # Add some space between the objects
                   tags$br(),  # Adds a single line break
                   actionButton("noDrivers", "No Drivers")
                 ),
                 mainPanel(
                   class="main-panel", # New insertion
                   
                   checkboxGroupInput("relevance",
                                      HTML("<b>Is the <span style='background-color: orange; padding: 2px; border-radius: 3px;'>gene</span> directly involved in chondrogenesis?</b>"),
                                      c("Yes", "No", "Unclear")),
                   conditionalPanel(condition = "input.relevance.includes('Yes')",
                                      checkboxGroupInput("proof",
                                      HTML("<b>What is the proof of the relationship <span style='background-color: orange; padding: 2px; border-radius: 3px;'>gene</span>-chondrogenesis?</b>"),
                                      c("Biomarkers", "Phenotypic", "Biomarkers+Phenotypic", "Unclear/Not Defined"))),
                   checkboxGroupInput("typeAss",
                                      HTML("<b>Is the <span style='background-color: orange; padding: 2px; border-radius: 3px;'>gene</span> the focus of study or cited as background information? (optional)</b>"),
                                      c("Focus", "Background Knowledge", "Unclear")),
                   checkboxGroupInput("typeExp",
                                      HTML("<b>Is the <span style='background-color: orange; padding: 2px; border-radius: 3px;'>gene</span> associated with in vitro or in vivo experiments? (optional)</b>"),
                                      c("In vivo", "In vitro")),
                   actionButton("button", "Next Sentence"), #This button will make go to the next sentence
                   actionButton("reverse", "Previous Sentence"),
                   actionButton("save", "Save"), # This does not do anything for now
                   
                   # Progress bar
                   div(id = "progress-container",
                       style = "margin-top: 20px;
                                max-width: 500px", # Lets make it wide so the number can be seen
                       div(
                         style = "text-align: center;
                         margin-bottom: 0px;
                         font-weight: bold;
                         line-height: 1.2;
                         font-size: 14px;",
                         "Progress through sentences"
                       ),
                       div(style = "margin-top: 0px; padding-top: 0px;",
                           uiOutput("progress_bar"))
                       )
                   
               )
              ),

             tags$style(HTML("
                             .main-panel{
                             min-height:600px;
                             overflow-y:auto
                             }
                             
                             .progress {
                                height: 20px !important;         /* Thicker container */
                                background-color: #e9ecef;
                                border-radius: 15px;
                                overflow: hidden;
                              }
                             
                             .progress-bar {
                              height: 20px !important; /*important to be the same height as progress*/
                             }"))
             
             ),
    # Instructions Window ####
    tabPanel("Instructions",
               h2("Introduction", style = "color:#2196F3"),
               wellPanel(
                 style = "background-color: #efebeb; padding: 20px; border-radius: 12px; box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.1); font-size: 18px; color: #2c3e50;",
                 HTML("<p>This page will guide you through curation and labelling (define the properties of the sentence in our case), explaining <b>why</b> we label, <b>what</b> is being labelled, and <b>how</b> to label it correctly within the app. In the end, you'll find helpful examples to guide your labelling tasks.</p>
                    <p>If you encounter any unclear instructions, don't hesitate to visit the 'Rules' tab for more detailed information on the decision-making criteria.</p>"),
                 
               ),
               
               div(style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                   h4("Why are we labelling?", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                   p("The ultimate goal is to develop a text-mining model capable of automatically extracting genes to create a dataset of genes associated with chondrogenesis based on scientific literature, which can be continuously updated."),
                   p("This dataset can be used for various applications, such as building knowledge graphs, mapping biological processes, and integrating with omics data. To achieve this, we need high-quality, manually curated data. This curated data will serve as the ground truth for training and validating our model(s), ensuring accurate and reliable predictions.")),
               br(),
               div(style = "background-color: #efebeb; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                   h4("What are we labelling?", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                   p("You will be labelling sentences from abstracts related to chondrogenesis. Before being shown in the app, the sentences are pre-processed to ensure they contain at least one gene and a concept related to chondrogenesis development."),
                   p("The app will only display sentences that have not been labelled yet. For each sentence, you will first see all the genes detected by GNorm2. Then, you will be presented with the specific gene to label inside that sentence; this gene will be highlighted in orange. You need to label this highlighted gene by defining its properties.")),
               h2("🖥️ Tabs Overview", style= "color:#2196F3"),
               
               # Start Window explanation
               h3("Start Window"),
               p("This is your starting point, the first tab that you will see when opening the app. Here you will find a brief overview of what the app does and wher do you need to do next based on what you want to achieve. Wheter you ened to define who you are, check the labelling rules or directly label, use this screen to get oriented and choose the right tab."),
               img(src = "start_window.png", style = "max-width: 100%; border-radius: 8px; box-shadow: 2px 2px 10px #ccc;text-align:cente;"),  
               br(),
             
               # User window explanation
               h3("User Window"),
               p("In the User window, you'll see a dropdown menu where you need to select your name before starting. This ensures that you can read, edit, and save your own file while labeling sentences, without affecting anyone else's work. If you switch to a different user, a new session will start, and the file will reload—only showing the sentences that haven’t been labeled yet. This helps keep everything organized and makes sure no sentences get labeled twice."),
               img(src = "user_window.png", style = "max-width: 100%; border-radius: 8px; box-shadow: 2px 2px 10px #ccc;text-align:cente;"),  
               br(),
             
               # Label window Explanation
               h3("Label Window"),
               p("Window where the unlabelled sentences of the session will be displayed, can be labelled and reported in case of an error"),
               p("A session, in this program, is described as the state of the file to label when opened, which can be when the app opened or when you changed users. If a sentence has been labelled and saved, the sentence has no drivers or the gene has been reported in a session it wont appear in the next one"),
             bsCollapse(id = "collapsePanels", open = NULL,
                          bsCollapsePanel("Sentence Display Section", 
                                          h3("Overview", style = "font-size: 23px;"),
                                          p("This section displays the sentence  that is being labelled and highlights the gene, in orange, that is being labelled. As well, for some context, all of the genes in that sentence are also highlighted in blue", style = "font-size: 16px;"),
                                          img(src = "sentence_display.png", style = "max-width: 100%; border-radius: 8px; box-shadow: 2px 2px 10px #ccc;text-align:cente;"),
                                          h4("What You See Here:", style = "font-size: 18px;"),
                                          
                                          tags$ul(
                                            tags$li(strong("Gene to Label:"), " Shows the full sentence with the gene that is currently being labelled. The options selected will be only recorded for this highlighted piece of text"),
                                            tags$li(strong("Report NOT A GENE Button:"), " Click to flag an incorrect gene. The system will record this and move to the next gene in the sentence. If you change your mind and you are still in the same session, you can click in the same button and that gene will be tagged again as a gene"),
                                            tags$li(strong("Sentence with All Genes:"), " Shows the full sentence with all gene mentions highlighted."),
                                            tags$li(strong("Report MORE GENES Button:"), " Click this if genes are missing  in the sentence and specify the number."),
                                            tags$li(strong("Report NO DRIVERS Button:"), " Click here if all of the blue highlithed genes are not drivers (genes are not directly involved in chondrogenesis) to label all of the highlighted text at the same time. In the next session none of the sentences will appear.")
                                          )
                          ),
                          
                          bsCollapsePanel("Gene Labelling Section",
                                          h3("Overview", style = "font-size: 23px;"),
                                          p("This section contains fields to label the highlighted orange gene and describe its association with chondrogenesis.", style = "font-size: 16px;"),
                                          img(src = "gene_labelling_section.png", style = "max-width: 100%; border-radius: 8px; box-shadow: 2px 2px 10px #ccc;text-align:cente;"),
                                          img(src = "gene_labelling_section_extended.png", style = "max-width: 100%; border-radius: 8px; box-shadow: 2px 2px 10px #ccc;text-align:cente;"),
                                          h4("Fields to Complete:", style = "font-size: 18px;"),
                                          tags$ul(
                                            tags$li(strong("Involvement with Chondrogenesis (Mandatory):"), " Mark 'Yes' if the gene is associated with cartilage development; mark 'No' if it is not and 'Unclear' otherwise. If you doubt about what to mark go to the Rules tab of the app"),
                                            tags$li(strong("Proof of the involvement (Mandatory if 'Yes' in involvement check box):"), " This check box will appear if the previous check box is select as 'Yes'. You should select Biomarkers if the proof that the provides about the gene being involved in chondorgenesis is only the expression of cartilage development biomarkers such as ACAN. Mark 'Phenotypic' if the expressed proofs are the development of cartilage in cell culture, for example; mark 'Biomarkers+Phenotypic' if both proofs are given and 'Unclear' otherwise."),
                                            tags$li(strong("Type of Association (Optional):"), " Specify if the gene is the focus of the study, if it comes from background knowledge or if it is unclear."),
                                            tags$li(strong("Type of Experiment (Optional):"), " Identify whether the data is based on an in vivo or in vitro experiment.")
                                          )
                          ),
                          
                          bsCollapsePanel("Navigation & Saving Section", 
                                          h3("Overview", style = "font-size: 23px;"),
                                          p("This section contains buttons for navigating through sentences and saving your work.", style = "font-size: 16px;"),
                                          img(src = "navigation_saving_section.png", style = "max-width: 100%; border-radius: 8px; box-shadow: 2px 2px 10px #ccc;text-align:cente;"),
                                          h4("How It Works:", style = "font-size: 18px;"),
                                          tags$ul(
                                            tags$li(strong("Next & Previous Sentence Buttons:"), " Move between different sentences."),
                                            tags$li(strong("Progress Bar:"), " Shows how far you are in the file."),
                                            tags$li(strong("Save Button:"), " Saves your selection for the sentence/gene. If not saved, the work won’t be recorded."),
                                            tags$li("Once a sentence/gene is saved, it will no longer appear for labeling in future sessions.")
                                          )
                                          
                          )
               ),
               
               h3("Rule Window"),
               p("In this window, you'll see some information about the rules that all of curators need to follow when deciding if a gene is relevant, not relevant or unclear"),
               img(src = "rules_window_original.png", style = "max-width: 100%; border-radius: 8px; box-shadow: 2px 2px 10px #ccc;text-align:cente;"),  
             
               # Steps to follow to label the gene(s) inside of a sentence
               h2("👣 Steps to label sentences", style = "color:#2196F3"),
               div(style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1);
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Step 1 - Select User"),
                 p("Each user has a file where their labeled sentences are stored. To begin, select your name from the dropdown menu. This ensures that you can read, edit, and save your own labeled data. If there are no sentences left for you to label, a warning will appear in the bottom right corner of the window."),
               ),
               br(),
               div(style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1);
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Step 2 - Move to Label window"),
                 p("Once you’ve selected your user, navigate to the Label Window. Here, you can:"),
                 tags$ul(
                  tags$li("Fill in the fields with the correct answers related to the association between genes and chondrogenesis for each sentence."),
                  tags$li("Report errors if you find any issues."),
                  tags$li("Move through the sentences using the navigation options.")
                 ),
                 p("For more details on how this window works, refer to the Label Window section of this instruction page.")
               ),
               br(),
               div(style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1);
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Step 3 - Save your work"),
                 p("After selecting the correct options for each sentence, make sure to click the Save button. If you move to the next sentence without saving, your selections will not be stored."),
               ),
               br(),
               div(style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1);
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Step 4 - (Optional) Re-label Sentences"),
                 p("As you go through the sentences, you will see the saved options for those labeled in the current session. If necessary, you can update your selections."),
                 p("Once you close the app or switch users (which starts a new session), all changes from previous sessions are final and cannot be modified.")
               )
               
    ),
    # Rules Window ####
    tabPanel("Rules", # name of the tab
             h2("Consistency in Sentence Labeling", style = "color:#2196F3"),
             
             wellPanel(
               style = "background-color: #efebeb; padding: 20px; border-radius: 12px; box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.1); font-size: 18px; color: #2c3e50;",
               HTML("<strong>Multiple curators</strong> are involved in labeling these sentences. To ensure that everyone follows the same approach and <strong>maintains consistency</strong> in the labeling process, we have established a clear set of rules. These guidelines help avoid misunderstandings and ensure high-quality, reliable data."),
               HTML("<strong>Following these guidelines will help maintain consistency and improve the quality of labeled data for training the machine learning model.</strong>")
             ),
             
             div(
               style = "text-align: center; font-size: 25px; font-weight: bold; 
               color: #2c3e50; background-color: #eaf2f8; padding: 12px; 
               border-left: 6px solid #2980b9; border-radius: 10px; margin-top: 15px;",
               "💡 Important Reminder: When in doubt, check the rules. If you are still uncertain, select 'Unclear' in the options."
             ),
             
             h2("📜 Set of Rules", style = "color:#2196F3"),
             
             # Rule Cards
             div(
               style = "display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; margin-top: 10px;",
               
               # Rule 1
               div(
                 style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Clear Gene-Chondrogenesis Relationship", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("The relationship between the gene and chondrogenesis must be explicitly stated in the text. Do not rely on external knowledge or inference to determine relevance."),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("In addition, caMsx2 overexpression induced Ihh (Indian hedgehog) expression in mouse primary chondrocytes.",
                   style = "font-style: italic;"),
                 p("In this sentence we will ",strong("NOT")," consider that ",em("caMsx2")," is directly involved in chondrogenesis even if we know that IHH is a well-known regulator of chondrogenesis, we cannot know that from the text")
               ),
               
               # Rule 2
               div(
                 style = "background-color: #EFEBEB; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Direct Relation to Chondrogenesis Only", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("Only genes that are directly involved in chondrogenesis (or chondrogenesis potential) should be labeled as related. Associations with general proliferation indicators should not be considered unless it is specified that is chondrogenesis related."),
                 h4("Examples of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("IGFBP3-knockout MESCs culture acquired chondrocyte-like features, such as cell condensation and aggregation.",
                   style = "font-style: italic;"),
                 p("In this sentence we will ",strong("NOT")," consider that ",em("IGFBP3")," is directly involved in chondrogenesis because it agreggation and proliferation are very general terms that are not only chondrogenesis specific"),
                 p("Over-expression of Aire induced the early stages of chondrocyte differentiation by facilitating expression of Bmp2.",
                   style = "font-style: italic;"),
                 p("In this case, we ",strong("WILL")," consider that ",em("Aire")," is a chondrogenesis driver due to inducing early stages of the process we are studying")
               ),
               
               # Rule 3
               div(
                 style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Modal verbs", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("Genes which proof uses modal verbs such as ",em("may"),", ",em("might")," or ",em("could")," are considered speculative and should not be classified as evidence of chondrogenesis"),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("Differential mRNA expression of TGF-beta1 was found during all passages, which suggests that this growth factor might be involved in chondrocyte.",
                   style = "font-style: italic;"),
                 p("In this sentence we will ",strong("NOT")," consider that ",em("TGF-beta1")," is directly involved in chondrogenesis")
               ),
               
               # Rule 4
               div(
                 style = "background-color: #EFEBEB; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Negative evidence", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("Do NOT consider negative evidence. If a gene ",em("supports another process")," and does not influence chondrogenesis directly, it is not counted as being involved in chondrogenesis."),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("Knockdown of FOXA2 promoted osteogenic differentiation of bone-marrow-derived mesenchymal stem cells while not altering chondrogenic potential",
                   style = "font-style: italic;"),
                 p("In this sentence we will ",strong("NOT")," consider that ",em("FOXA2")," is directly involved in chondrogenesis because it indicates no effect on chondrogenesis, i.e., negative evidence.")
               ),
               
               # Rule 5
               div(
                 style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Pathways and axis", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("Genes that are part of chondrogenic pathways or axes should not be classified as drivers when mentioned as intermediates or downstream markers. In such cases, they serve as evidence (phenotypic or biomarker proof) that another gene acts as a regulator of chondrogenesis."),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("Cytl1 exerted its chondrogenic effect via stimulation of Sox9 transcriptional activity",
                   style = "font-style: italic;"),
                 p("In this sentence we will consider that ",em("Cytl1")," is directly involved in chondrogenesis but ",strong("NOT")," ",em("SOX9")," which in this case acts as a intermediary")
               ),
               
               # Rule 6
               div(
                 style = "background-color: #EFEBEB; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Exclusion of Hypertrophy and Osteogenesis", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("Genes related to hypertrophy (also referred to as ",em("terminal chondrogenesis")," or ",em("terminal maturation"),") or reduced osteogenesis should not be labeled as related to chondrogenesis."),
                 p(strong("IMPORTANT: "),"terminal maturation is not the same as maturation, the latter is a wider process."),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("FOXC1 and FOXC2 regulate growth plate chondrocyte maturation towards hypertrophy in the embryonic mouse limb skeleton.",
                   style = "font-style: italic;"),
                 p("In this sentence we will ",strong("NOT")," consider that ",em("FOXC1")," and ", em("FOXC2")," are directly involved in chondrogenesis because the regulation is towards hypertrophic cells, not to chondrocytes")
               ),
               
               # Rule 7
               div(
                 style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Exclusion of Cell Proliferation, Re-differentiation and Repair", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("Genes related to only cell proliferation or cartilage repair or re-differentiation should not be labeled as related to chondrogenesis."),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("We found that silencing of miR-221 strongly enhanced in vivo cartilage repair compared to the control conditions.",
                   style = "font-style: italic;"),
                 p("In this sentence we will ",strong("NOT")," consider that ",em("miR-221")," is directly involved in chondrogenesis because it is only mentioned to have an effect on cartilage reparation, not specifically chondrogenesis")
               ),
               
               # Rule 8
               div(
                 style = "background-color: #EFEBEB; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Cross-Species Consideration", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("Information from all species is valid and should be taken into account when labeling."),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("Importantly, TET1 inhibition in vivo in late stages of a mouse model of OA led to increased cartilage regeneration.",
                   style = "font-style: italic;"),
                 p("In this sentence we ",strong("WILL")," consider that ",em("TET1")," is directly involved in chondrogenesis even if the research has been done in a mouse model")
               ),
               
               # Rule 9
               div(
                 style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Cell types Consideration", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("We will consider all types of cells-lines for the search of chondorgenesis dirvers"),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("In Conclusion, our data implies that miR-140 is a potent chondrogenic differentiation inducer for iPSCs and also, we have showed increasing chondrogenic differentiation by using overexpression of miR-140 and TGFb3.",
                   style = "font-style: italic;"),
                 p("In this sentence we ",strong("WILL")," consider that ",em("miR-140")," and ",em("TGFb3"),"  are directly involved in chondrogenesis")
               ),
               
               # Rule 10
               div(
                 style = "background-color: #EFEBEB; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Tri-lineage cells Consideration", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("In this dataset, any sentence mentioning ",em("tri-lineage cells")," should be treated as indicating chondrocytes, osteoblasts and adipocytes, since our data acquirement was focused on chondrogenesis."),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("We have shown that overexpression of Sox11 in rMSCs by lentivirus-mediated gene transfer leads to enhanced tri-lineage differentiation and accelerated bone formation in fracture model of rats.",
                   style = "font-style: italic;"),
                 p("In this sentence we ",strong("WILL")," consider that ",em("Sox11")," is directly involved in chondrogenesis because enhances the tri-lineage differentiation")
               ),
               
               # Rule 11
               div(
                 style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("All biomolecules Considered", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("We will be considering a less strict definition of gene. This means that protein coding and non coding genes will be considered, in addition to moleculares as microRNAs"),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("Knockdown of miR-145 promoted chondrogenesis and inhibited hypertrophy differentiation in RMCs.",
                   style = "font-style: italic;"),
                 p("In this sentence we ",strong("WILL")," consider that ",em("miR-145")," is directly involved in chondrogenesis")
               ),
               
               # Rule 12
               div(
                 style = "background-color: #EFEBEB; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Bio markers relations", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("We will be considering drivers related to the expression of chondrogenesis biomarkers such as ACAN, SOX9, etc only if there is another specifications in the text that they are specific chondrogenesis markers. We will not consider the genes drivers if the already known biomarkers are by themself."),
                 p("If in the text only biomarkers are shown as proof, the biomarker proff box needs to be selected  when labelling the text"),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("Furthermore, Arid5a physically interacted with Sox9 in nuclei and up-regulated the chondrocyte-specific action of Sox9.",
                   style = "font-style: italic;"),
                 p("In this sentence we ",strong("WILL")," consider that ",em("Arid5a")," is directly involved in chondrogenesis because it is implied that influences the expression of a chondrocyte specific marker."),
                 p("Furthermore, Arid5a physically interacted with Sox9 in nuclei and up-regulated the action of Sox9.",
                   style = "font-style: italic;"),
                 p("In this sentence we will",strong("NOT")," consider that ",em("Arid5a")," is directly involved in chondrogenesis because it is just upregulating a gene, we dont have evidence that this gene is chondrogenesis marker.")
               ),
               
               # Rule 13
               div(
                 style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Mentioning of cartilage associated diseases", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("We will not consider markers of diseases related to chondrogenesis. Only because the disease is associated to chondrogenesis, we will not take it as a driver of this process"),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("Inhibiting the expression of CDKN1A can significantly suppress the differentiation of OA chondrocytes.",
                   style = "font-style: italic;"),
                 p("In this sentence we will ",strong("NOT")," consider that ",em("CDKN1A")," is involved in chondrogenesis only because it is associated with osteoarthrithis (OA)")
               ),
               
               # Rule 14
               div(
                 style = "background-color: #EFEBEB; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Functional Role vs Marker Role", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("Only label genes that are described as having a direct functional or regulatory role in chondrogenesis. If a gene is mentioned only as a marker or indicator of chondrogenesis, do not label it as directly involved."),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("Genome-wide mRNA expression analysis of the midpalatal suture tissue revealed that MLL4 is essential for the timely expression of major cartilage development genes, such as Col2a1 and Acan, at birth.",
                   style = "font-style: italic;"),
                 p("In this sentence we will consider that ",em("MLL4")," is directly involved in chondrogenesis but we will ",strong("NOT")," consider ",em("Col2a1")," and ",em("ACAN"), " as drivers because here they act as biomarkers of the process")
               ),
               
               # Rule 15
               div(
                 style = "background-color: #ffffff; padding: 15px; border-radius: 10px; 
                 box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1); width: 300px; text-align: center; 
                 border: 2px solid #bdc3c7; color: #2c3e50;",
                 h4("Growth Plate", style = "color: #2c3e50; font-size: 20px; font-weight: bold;"),
                 p("If the mention refers to the growth plate, it must be explicitly stated that the process involves chondrocytes."),
                 h4("Example of Rule", style = "color: #5251c1; font-size: 20px; font-weight: bold;"),
                 p("Sox9 is involved in the process of endochondral ossification within the growth plate.",
                   style = "font-style: italic;"),
                 p("In this sentence we will ",strong("NOT")," consider that ",em("Sox9")," is directly involved in chondrogenesis because in this example it is referring to osteoblasts in the groth plate and not chondrocytes")
               ),
               
             )
    )
  )
)


# Back-End ####
server <- function(input, output, session) {
  # initialize the checkboxes
  prev_selection_rel <- reactiveVal(0)
  prev_selection_ass <- reactiveVal(0)
  prev_selection_exp <- reactiveVal(0)
  prev_selection_proof <- reactiveVal(0)
  
  # Roots the user is allowed to browse from — adjust to where your CSVs actually live
  roots <- c(home = "C:/Users/...",
             wd = getwd()) # Change accordingly to the folder where the data will be hold
  shinyFileChoose(input, "file", roots = roots, session = session,
                  filetypes = c("csv"))
  
  # Initial default file path
  file_path <- reactiveVal(NULL)
  
  # Inital Values
  df <- reactiveValues(data = NULL) # We use reactiveValues because we need a malleable dataframe so we can change it at any time
  empty_label_rows <- reactiveVal(NULL)
  total_sentences <- reactiveVal(NULL)
  row_index <- reactiveVal(1)
  
  # Observer to update when input$file changes
  observeEvent(input$file, {
    req(input$file)
    
    selected <- parseFilePaths(roots, input$file)
    req(nrow(selected) > 0)
    
    candidate_path <- selected$datapath
    
    # Progress bar
    progress <- Progress$new(session, min = 0, max = 1)
    on.exit(progress$close())  # ensures it closes even if something errors out
    
    progress$set(message = "Reading file...", value = 0.3)
    
    # Try to read the file safely
    # just in case it is not correct or it will break the app
    new_data <- tryCatch({
      read.csv(candidate_path)
    }, error = function(e) {
      showNotification(
        paste("Could not read the file:", e$message),
        type = "error", duration = 5
      )
      NULL
    })
    
    if (is.null(new_data)) {
      progress$set(message = "Failed to read file", value = 1)
      Sys.sleep(1)  # brief pause so the message is actually visible before closing
      showNotification(paste0("Could not read '", basename(candidate_path), "' — it may not be a valid CSV."),
                       type = "error", duration = 5)
      return(NULL)
    }
    
    progress$set(message = "Checking file structure...", value = 0.6)
    
    # Stop here if reading failed
    req(new_data)
    
    # Define the columns your app actually needs
    # these columns can also change depending on what you are recording with teh app
    required_cols <- c("pmid", "number", "sentence", "allGenesIndexStart", "allGenesIndexEnd", "indexStart", "indexEnd",
                       "association", "experiment", "proof", "errorReported", "errorMoreGenes",
                       "numberGenesTotal", "label", "NotGeneError")
    missing_cols <- setdiff(required_cols, names(new_data))
    
    if (length(missing_cols) > 0) {
      progress$set(message = "Invalid file structure", value = 1)
      Sys.sleep(1)
      showNotification(paste0("'", basename(candidate_path), "' is missing required column(s): ",
                              paste(missing_cols, collapse = ", ")),
                       type = "error", duration = 6)
      return(NULL)  # abort — don't update file_path or df$data
    }
    
    # check that the csv it's not empty
    if (nrow(new_data) == 0) {
      progress$set(message = "File is empty", value = 1)
      Sys.sleep(1)
      showNotification(paste0("'", basename(candidate_path), "' has no rows."),
                       type = "error", duration = 5)
      return(NULL)
    }
    
    progress$set(message = "Loaded", value = 1)
    # now that we have done all of the checks we can then try to upload it
    # Update the file path based on the selected file
    file_path(selected$datapath)
    
    # Read the new data from the CSV and store it in df$data
    df$data <- read.csv(file_path())
    
    # Update empty label rows and total sentences based on the new data
    empty_label_rows(which(is.na(df$data$label) & is.na(df$data$NotGeneError)))
    
    total_sentences(length(empty_label_rows()))
    
    if (total_sentences() == 0){
      showNotification("No sentences without labelling for this file, choose another file", type = "error", duration = 3)
    }
    
    # Reset the row index
    row_index(1)
  })
  
  # Show what file we are changing
  output$fileEdited <- renderText({HTML(paste0("You are currently editing the file: <b>", file_path(),"</b>"))})
  
  #Show the sentence with all the genes of the row with row_index
  output$sentenceComplete <- renderUI({
    indexes_end <- df$data$allGenesIndexEnd[empty_label_rows()[row_index()]]
    indexes_end <- gsub(" ", "", indexes_end)  # Remove spaces
    indexes_end <- strsplit(indexes_end, ",")  # Split by commas
    # Convert the elements to numeric
    indexes_end <- as.numeric(indexes_end[[1]])
    
    indexes_start <- df$data$allGenesIndexStart[empty_label_rows()[row_index()]]
    indexes_start <- gsub(" ", "", indexes_start)  # Remove spaces
    indexes_start <- strsplit(indexes_start, ",")  # Split by commas
    # Convert the elements to numeric
    indexes_start <- as.numeric(indexes_start[[1]])
    
    HTML(highlight_genes(df$data$sentence[empty_label_rows()[row_index()]], indexes_start, indexes_end, "lightblue"))
  })
  
  #Show the sentence of the row with row_index
  output$sentence <- renderUI({
    # Define the variables that are going to change everytime we change row_index
    text <- df$data$sentence[empty_label_rows()[row_index()]]
    start_gene <- df$data$indexStart[empty_label_rows()[row_index()]]
    end_gene <- df$data$indexEnd[empty_label_rows()[row_index()]]
    
    
    highlighted_text <- highlight_genes(df$data$sentence[empty_label_rows()[row_index()]], start_gene, end_gene, "orange")
    
    if (!is.na(df$data$NotGeneError[empty_label_rows()[row_index()]]) && df$data$NotGeneError[empty_label_rows()[row_index()]] == TRUE)  {
      # Append "Reported" next to the sentence if errorNonGene is TRUE
      tagList(
        HTML(highlighted_text),
        tags$span(style = "color: red; font-weight: bold;", "Reported As Non-Gene")  # Red text for "Reported"
      )
    } else {
      # Just display the sentence if errorNonGene is not TRUE
      HTML(highlighted_text)
    }
    
  })
  
  # Lets define what button is going to be in the place of our dynamicButton
  output$dynamicButton <- renderUI({
    if (!is.na(df$data$NotGeneError[empty_label_rows()[row_index()]]) && df$data$NotGeneError[empty_label_rows()[row_index()]] == TRUE){
      actionButton("geneButton", "It is a gene")
    }
    else{
      actionButton("notGene", "Not a gene")
    }
  })
  
  # Function to update the progress bar based on row_index
  observe({
    row_idx <- row_index()  # Get the current row index
    progress_percentage <- (row_idx / total_sentences()) * 100
    
    # Render progress bar dynamically with the required 'id' argument
    output$progress_bar <- renderUI({
      progressBar(id = "progress_bar",    # Add an ID to the progress bar
                  value = progress_percentage, 
                  display_pct = TRUE,    # Show percentage on the bar
                  striped = TRUE,        # Add stripes
                  status = "success"     # Set the color (success is green)
      )
    })
  })
  
  
  # Set what happen when we press the button next
  observeEvent(input$button, {
    if (row_index() < length(empty_label_rows())){
      row_index(row_index() + 1)
      # Reset the values of the boxes
      updateCheckboxGroupInput(session, "relevance", selected = df$data$label[empty_label_rows()[row_index()]])
      updateCheckboxGroupInput(session, "typeAss", selected = df$data$association[empty_label_rows()[row_index()]])
      updateCheckboxGroupInput(session, "typeExp", selected = df$data$experiment[empty_label_rows()[row_index()]])
      updateCheckboxGroupInput(session, "proof", selected = df$data$proof[empty_label_rows()[row_index()]])
      # reset values for previous selections as well
      prev_selection_rel(df$data$label[empty_label_rows()[row_index()]])
      prev_selection_ass(df$data$association[empty_label_rows()[row_index()]])
      prev_selection_exp(df$data$experiment[empty_label_rows()[row_index()]])
      prev_selection_proof(df$data$proof[empty_label_rows()[row_index()]])
    }
    else{
      showNotification("This is the last unlabelled sentence, no more to show", type="warning", duration = 3)
    }
  })
  
  # Go to previous sentence
  observeEvent(input$reverse, {
    if (row_index() <= 1){
      showNotification("This is the first unlabelled sentence, cannot go further back", type="warning", duration = 3)
    }
    else{
      row_index(row_index() - 1)
      
      # Reset the values of the boxes
      updateCheckboxGroupInput(session, "relevance", selected = df$data$label[empty_label_rows()[row_index()]])
      updateCheckboxGroupInput(session, "typeAss", selected = df$data$association[empty_label_rows()[row_index()]])
      updateCheckboxGroupInput(session, "typeExp", selected = df$data$experiment[empty_label_rows()[row_index()]])
      updateCheckboxGroupInput(session, "proof", selected = df$data$proof[empty_label_rows()[row_index()]])
      # reset values for previous selections as well
      prev_selection_rel(df$data$label[empty_label_rows()[row_index()]])
      prev_selection_ass(df$data$association[empty_label_rows()[row_index()]])
      prev_selection_exp(df$data$experiment[empty_label_rows()[row_index()]])
      prev_selection_proof(df$data$proof[empty_label_rows()[row_index()]])
    }
    
  })
  
  # Save the selections that we have
  observeEvent(input$save, {
    # Lets check that relevance is checked
    if (length(input$relevance) == 0){
      showNotification("Relevance needs to be checked to be saved!", type="error", duration = 3)
    }
    # Check that if relevance is yes we need to have as well proof
    else if ("Yes" %in% input$relevance && length(input$proof) == 0){
      showNotification("If the gene is related to chondrogenesis the proof of that need to be cheked!", type="error", duration = 3)
    }
    else {
      # Let's save the 3 fields on the row
      df$data$label[empty_label_rows()[row_index()]] <- input$relevance
      df$data$association[empty_label_rows()[row_index()]] <- ifelse(length(input$typeAss) == 0, NA, input$typeAss)
      df$data$experiment[empty_label_rows()[row_index()]] <- ifelse(length(input$typeExp) == 0, NA, input$typeExp)
      if ("Yes" %in% input$relevance){
        df$data$proof[empty_label_rows()[row_index()]] <- input$proof
      }
      else{
        df$data$proof[empty_label_rows()[row_index()]] <- NA
      }
      
      # save the database in the file everytime a sentence is saved
      write.csv(df$data, file_path(), row.names = FALSE)
      
      showNotification("Sentence Label Saved!", type = "message", duration = 3)
      
      if (row_index() < length(empty_label_rows())){
        row_index(row_index() + 1)
        # Reset the values of the boxes
        updateCheckboxGroupInput(session, "relevance", selected = df$data$label[empty_label_rows()[row_index()]])
        updateCheckboxGroupInput(session, "typeAss", selected = df$data$association[empty_label_rows()[row_index()]])
        updateCheckboxGroupInput(session, "typeExp", selected = df$data$experiment[empty_label_rows()[row_index()]])
        updateCheckboxGroupInput(session, "proof", selected = df$data$proof[empty_label_rows()[row_index()]])
        # reset values for previous selections as well
        prev_selection_rel(df$data$label[empty_label_rows()[row_index()]])
        prev_selection_ass(df$data$association[empty_label_rows()[row_index()]])
        prev_selection_exp(df$data$experiment[empty_label_rows()[row_index()]])
        prev_selection_proof(df$data$proof[empty_label_rows()[row_index()]])
        }
      else{
        showNotification("That was the last unlabelled sentence, no more to show", type="message", duration = 3)
      }
    }
  })
  
  # Report an error on the gene side of the sentence
  observeEvent(input$notGene, {
    # If not gene that part of the sentence will not have anything selected and will go directly to next sentence
    # As well the warning field of that sentence will be updated
    
    # We write th error in the table
    df$data$NotGeneError[empty_label_rows()[row_index()]] <- TRUE
    
    # save the database in the file every time a sentence is saved
    write.csv(df$data, file_path(), row.names = FALSE)
    
    # Give message to user
    showNotification("Thanks for reporting the NON gene!", type="message", duration = 3)
    
    if (row_index() < length(empty_label_rows())){
      row_index(row_index() + 1)
      # Reset the values of the boxes
      updateCheckboxInput(session, "relevance", value = NA)
      updateCheckboxInput(session, "typeAss", value = NA)
      updateCheckboxInput(session, "typeExp", value = NA)
      updateCheckboxInput(session, "proof", value = NA)
      # reset values for previous selections as well
      prev_selection_rel(0)
      prev_selection_ass(0)
      prev_selection_exp(0)
      prev_selection_proof(0)
    }
    else{
      showNotification("That was the last unlabelled sentence, no more to show", type="message", duration = 3)
    }
  })
  
  observeEvent(input$geneButton,{
    # We over-write th error in the table
    df$data$NotGeneError[empty_label_rows()[row_index()]] <- NA
    
    # save the database in the file everytime a sentence is saved
    write.csv(df$data, file_path(), row.names = FALSE)
    
    showNotification("This text is marked as a gene again!", type="message", duration = 3)
    
    row_index(row_index()) # We "update" the row_index so the sentence can be updated without the tag
  })
  
  # Here is going to be the code that will make the boxes only be able to select one
  # We need to do it separately with the 3 checkbox because they are independent
  observeEvent(input$relevance,{
    if (length(input$relevance) > 1){
      new_selection_rel <- setdiff(input$relevance, prev_selection_rel())
      updateCheckboxGroupInput(session, "relevance", selected = new_selection_rel)
    }
    # update the prev_selection value
    prev_selection_rel(input$relevance)
  })
  
  observeEvent(input$proof,{
    if (length(input$proof) > 1){
      new_selection_proof <- setdiff(input$proof, prev_selection_proof())
      updateCheckboxGroupInput(session, "proof", selected = new_selection_proof)
    }
    # update the prev_selection value
    prev_selection_proof(input$proof)
  })
  
  observeEvent(input$typeAss,{
    if (length(input$typeAss) > 1){
      new_selection_ass <- setdiff(input$typeAss, prev_selection_ass())
      updateCheckboxGroupInput(session, "typeAss", selected = new_selection_ass)
    }
    # update the prev_selection value
    prev_selection_ass(input$typeAss)
  })
  
  observeEvent(input$typeExp,{
    if (length(input$typeExp) > 1){
      new_selection_exp <- setdiff(input$typeExp, prev_selection_exp())
      updateCheckboxGroupInput(session, "typeExp", selected = new_selection_exp)
    }
    # update the prev_selection value
    prev_selection_exp(input$typeExp)
  })
  
  # Report error of more genes, the button moreGenes
  observeEvent(input$moreGenes, {
    output$dynamic_ui <- renderUI({
      tagList(
        numericInput("num_input", "Enter the total number of genes", value = NULL),
        actionButton("save_report", "Save Report"),
        actionButton("cancel_moreGenes", "Cancel")
      )
    })
  })
  
  # Button to save that there is no driver in the whole sentence
  # Checking 
  # After I have coded I need to check it that everything is okay because a lot of errors
  # could have happened
  observeEvent(input$noDrivers,{
    # with this button we will save as no drivers the current sentence and also
    # all of the ones with the same pmid
    pmid_sentence <- df$data$pmid[empty_label_rows()[row_index()]]
    number_sentence <- df$data$number[empty_label_rows()[row_index()]]
    number_rows_pmid <- nrow(df$data[df$data$pmid == pmid_sentence & df$data$number == number_sentence,])
    if (number_rows_pmid == 1){ # Slightly modified save button effect
      # Let's save the 4 fields on the row
      df$data$label[empty_label_rows()[row_index()]] <- "No"
      df$data$association[empty_label_rows()[row_index()]] <- NA
      df$data$experiment[empty_label_rows()[row_index()]] <- NA
      df$data$proof[empty_label_rows()[row_index()]] <- NA
      
      # save the database in the file everytime a sentence is saved
      write.csv(df$data, file_path(), row.names = FALSE)
      
      showNotification("Sentence Label Saved!", type = "message", duration = 3)
      
      if (row_index() < length(empty_label_rows())){
        row_index(row_index() + 1)
        # Reset the values of the boxes
        updateCheckboxGroupInput(session, "relevance", selected = df$data$label[empty_label_rows()[row_index()]])
        updateCheckboxGroupInput(session, "typeAss", selected = df$data$association[empty_label_rows()[row_index()]])
        updateCheckboxGroupInput(session, "typeExp", selected = df$data$experiment[empty_label_rows()[row_index()]])
        updateCheckboxGroupInput(session, "proof", selected = df$data$proof[empty_label_rows()[row_index()]])
        # reset values for previous selections as well
        prev_selection_rel(df$data$label[empty_label_rows()[row_index()]])
        prev_selection_ass(df$data$association[empty_label_rows()[row_index()]])
        prev_selection_exp(df$data$experiment[empty_label_rows()[row_index()]])
        prev_selection_proof(df$data$proof[empty_label_rows()[row_index()]])
      }
      else{
        showNotification("That was the last unlabelled sentence, no more to show", type="message", duration = 3)
      }
    }
    else{ # There is more than 1 sentence of that PMID and number
      # Check if some of them are already labelled as yes drivers
      number_already_labelled <- nrow(df$data[(df$data$pmid == pmid_sentence & df$data$number == number_sentence) & !is.na(df$data$label),])
      if (number_already_labelled == 0){ # No sentence has been labelled yet
        # We need to label all of the sentences with that pmid and number
        # Let's save the 4 fields on the row for all the sentences
        df$data$label[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- "No"
        df$data$association[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- NA
        df$data$experiment[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- NA
        df$data$proof[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- NA
        
        # save the database in the file everytime a sentence is saved
        write.csv(df$data, file_path(), row.names = FALSE)
        
        showNotification(paste0(number_rows_pmid, " sentences have been labelled!"), type = "message", duration = 3)
        
        # Part of the save button effect (next sentence one)
        if (row_index() < length(empty_label_rows())){
          row_index(row_index() + 1)
          # Reset the values of the boxes
          updateCheckboxGroupInput(session, "relevance", selected = df$data$label[empty_label_rows()[row_index()]])
          updateCheckboxGroupInput(session, "typeAss", selected = df$data$association[empty_label_rows()[row_index()]])
          updateCheckboxGroupInput(session, "typeExp", selected = df$data$experiment[empty_label_rows()[row_index()]])
          updateCheckboxGroupInput(session, "proof", selected = df$data$proof[empty_label_rows()[row_index()]])
          # reset values for previous selections as well
          prev_selection_rel(df$data$label[empty_label_rows()[row_index()]])
          prev_selection_ass(df$data$association[empty_label_rows()[row_index()]])
          prev_selection_exp(df$data$experiment[empty_label_rows()[row_index()]])
          prev_selection_proof(df$data$proof[empty_label_rows()[row_index()]])
        }
        else{
          showNotification("That was the last unlabelled sentence, no more to show", type="message", duration = 3)
        }
      }
      else{ # There has been already labelled sentences
        number_already_labelled_drivers <- nrow(df$data[!is.na(df$data$pmid) & 
                                                        !is.na(df$data$number) & 
                                                        !is.na(df$data$label) &
                                                        (df$data$pmid == pmid_sentence & df$data$number == number_sentence) &
                                                        (df$data$label == "Yes" | df$data$label == "Unclear"),])
        # I needed to add the !is.na because if I didn't there would be an additional row with NA in everything
        if (number_already_labelled_drivers != 0){ # There has been labelled as yes or unclear drivers
          # Give the window of "are you sure? you are going to re-write #sentences that have been labelled as drivers.
          shinyalert(title = "Overwritting Warning",
                     text=paste0("Previously you have labelled ", number_already_labelled_drivers," gene(s) as drivers or unclear in this sentence.\nWith this action you will overwritte them as no drivers.\nAre you sure you want to continue?"),
                     type = "warning",
                     showCancelButton = TRUE,
                     showConfirmButton = TRUE,
                     confirmButtonText = "Continue",
                     inputId = "warningNoDriversAnswer",
                     size = "m")
          # The output of this shinyalert is going to be handled in the observe even with this alert
        }
        else{ # They are labelled with No so we overwrite them
          # We need to label all of the sentences with that pmid and number
          # Then we need to do the same protocol as save button
          # It is the same behaviour as if no sentences have been labelled
          
          # Let's save the 4 fields on the row for all the sentences
          df$data$label[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- "No"
          df$data$association[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- NA
          df$data$experiment[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- NA
          df$data$proof[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- NA
          
          # save the database in the file everytime a sentence is saved
          write.csv(df$data, file_path(), row.names = FALSE)
          
          showNotification(paste0(number_rows_pmid, " sentences have been labelled!"), type = "message", duration = 3)
          
          # Part of the save button effect (next sentence one)
          if (row_index() < length(empty_label_rows())){
            row_index(row_index() + 1)
            # Reset the values of the boxes
            updateCheckboxGroupInput(session, "relevance", selected = df$data$label[empty_label_rows()[row_index()]])
            updateCheckboxGroupInput(session, "typeAss", selected = df$data$association[empty_label_rows()[row_index()]])
            updateCheckboxGroupInput(session, "typeExp", selected = df$data$experiment[empty_label_rows()[row_index()]])
            updateCheckboxGroupInput(session, "proof", selected = df$data$proof[empty_label_rows()[row_index()]])
            # reset values for previous selections as well
            prev_selection_rel(df$data$label[empty_label_rows()[row_index()]])
            prev_selection_ass(df$data$association[empty_label_rows()[row_index()]])
            prev_selection_exp(df$data$experiment[empty_label_rows()[row_index()]])
            prev_selection_proof(df$data$proof[empty_label_rows()[row_index()]])
          }
          else{
            showNotification("That was the last unlabelled sentence, no more to show", type="message", duration = 3)
          }
        }
      }
      
    }
  })
  
  # A warning with the no drivers has been pop up meaning that there were labelled as drivers
  # some of the genes in the sentence
  observeEvent(input$warningNoDriversAnswer, {
    if (input$warningNoDriversAnswer == TRUE){ # They want to overwritte the gene input
      # We need to define again the pmid_sentence and number_sentence because it was in another environment
      pmid_sentence <- df$data$pmid[empty_label_rows()[row_index()]]
      number_sentence <- df$data$number[empty_label_rows()[row_index()]]
      number_rows_pmid <- nrow(df$data[df$data$pmid == pmid_sentence & df$data$number == number_sentence,])
      # We need to overwritte all the sentences and go to the next sentence, similar to other ifs in the script
      # Let's save the 4 fields on the row for all the sentences
      df$data$label[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- "No"
      df$data$association[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- NA
      df$data$experiment[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- NA
      df$data$proof[df$data$pmid == pmid_sentence & df$data$number == number_sentence] <- NA
      
      # save the database in the file everytime a sentence is saved
      write.csv(df$data, file_path(), row.names = FALSE)
      
      showNotification(paste0(number_rows_pmid, " sentences have been labelled!"), type = "message", duration = 3)
      
      # Part of the save button effect (next sentence one)
      if (row_index() < length(empty_label_rows())){
        row_index(row_index() + 1)
        # Reset the values of the boxes
        updateCheckboxGroupInput(session, "relevance", selected = df$data$label[empty_label_rows()[row_index()]])
        updateCheckboxGroupInput(session, "typeAss", selected = df$data$association[empty_label_rows()[row_index()]])
        updateCheckboxGroupInput(session, "typeExp", selected = df$data$experiment[empty_label_rows()[row_index()]])
        updateCheckboxGroupInput(session, "proof", selected = df$data$proof[empty_label_rows()[row_index()]])
        # reset values for previous selections as well
        prev_selection_rel(df$data$label[empty_label_rows()[row_index()]])
        prev_selection_ass(df$data$association[empty_label_rows()[row_index()]])
        prev_selection_exp(df$data$experiment[empty_label_rows()[row_index()]])
        prev_selection_proof(df$data$proof[empty_label_rows()[row_index()]])
      }
      else{
        showNotification("That was the last unlabelled sentence, no more to show", type="message", duration = 3)
      }
    }
    # If FALSE we dont need to do anything
  })
  
  observeEvent(input$save_report, {
    if (is.null(input$num_input) || input$num_input < 0){
      showNotification("To report this error, please introduce total number of genes in sentence!", type="error", duration = 3)
    }
    else{
      df$data$errorMoreGenes[empty_label_rows()[row_index()]] <- TRUE
      df$data$numberGenesTotal[empty_label_rows()[row_index()]] <- input$num_input
      
      # save the database in the file everytime a sentence is saved
      write.csv(df$data, file_path(), row.names = FALSE)
      
      showNotification("Error report Saved!", type = "message", duration = 3)
      
      # Remove input fields after saving
      output$dynamic_ui <- renderUI(NULL)
    }
    
  })
  
  observeEvent(input$cancel_moreGenes,{
    output$dynamic_ui <- renderUI({
      NULL
    })
  })
  
}

shinyApp(ui, server)