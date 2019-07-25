## FMRI & RELIGIOSITY STUDY ##
## IMPORT AND CONVERT LOG FILES ##

library(dplyr)
setwd('/home/lsnoek1/projects/PIOP1_new/code')
# create categories
female.C <- matrix(nrow=4,ncol=12)
female.I <- matrix(nrow=4,ncol=12)
male.C <- matrix(nrow=4,ncol=12)
male.I <- matrix(nrow=4,ncol=12)
for (i in 1:4){ 
  female.C[i,] <- seq(1, 12, 1) + i*100 #female congruent
  female.I[i,] <- seq(401, 412, 1) + i*100 #female incongruent
  male.I[i,] <- seq(13, 24, 1) + i*100 #male incongruent
  male.C[i,] <- seq(413, 424, 1) + i*100 #male congruent
} 

#combine overall categories 
female <- cbind(female.C, female.I)
male <- cbind(male.C,male.I)
congruent <- cbind(female.C,male.C)
incongruent <- cbind(female.I,male.I)

# behavioral data
all = data.frame()
nsub <- 250
sub <- c(1:250)
n = sprintf("%03d", 1:nsub)
file_name = paste0("pi0",n[sub],"-piopgstroop.log") 
for(i in 1:nsub) {
  files <- list.files("../logs/gstroop/raw")
  if (any(files %in% file_name[i])) {
    ## find .log read it in and append it
    # s149 has 5 extra rows op responses in the practice block for some reason... Need to be excluded. 
    if (i == 149){d <- read.delim(file= paste0("../logs/gstroop/raw/",file_name[i]), skip = 10, header = F)
    } else{
      d <- read.delim(file= paste0("../logs/gstroop/raw/",file_name[i]), skip = 5, header = F)
    }
    
    header <- scan(file = paste0("../logs/gstroop/raw/",file_name[i]), skip = 3, nlines = 1, sep = "\t", what = character())
    header[9] <- "Uncertainty2" #needs a unique name 
    colnames(d) <- header
    
    # remove practice block
    startexp <- match(255, d$Code)
    t_scan <- d$Time[startexp]      # onset of scanner
    d <- d[-(1:startexp), ]
    # select only useful colums 
    d <- d %>%
      select_(~Subject, ~Trial, ~`Event Type`, ~Code, ~Time, ~TTime, ~`Stim Type`)
    # remove rows with 'pulse' and with Picture 99
    d <- d[d$`Event Type`!="Pulse", ]
    d <- d[!(d$`Event Type`=="Picture" & d$Code == 99), ]
    # add condition
    d$Category[d$Code %in% female] <- "female"
    d$Category[d$Code %in% male] <- "male"
    d$Condition[d$Code %in% congruent] <- "congruent"
    d$Condition[d$Code %in% incongruent] <- "incongruent"
    for (c in 1:nrow(d)){ # female = resp 2 (right), male = resp 1 (left)
      d$Correct[c] <- ifelse(d$Category[c] == "female" & d$Code[c+1] == 2 
                             | d$Category[c] == "male" & d$Code[c+1] == 1 ,1,0)
      d$TTime[c] <- d$TTime[c+1]
      d$response_hand[c] <- d$Code[c+1] #1 is left, 2 is right
      c <- c+1}
    # s209 missed the last trial, therefore there is no response to record, and TTime and Correct are NA... 
    if (i==209){
      d$Correct[d$`Stim Type`=="miss"] <- 0
      d$TTime[d$`Stim Type`=="miss"] <- 0
    }
    d <- d[!(d$`Event Type`=="Response"), ]
    d$Number <- i
    d$response_type <- ifelse((d$`Stim Type`=="hit" & d$Correct==1),"correct","incorrect")
    d$response_type <- ifelse(d$`Stim Type`=="miss","miss",d$response_type)
    # dataframe with only relevant properties
    data <- d %>% 
      select_(~Number, ~Time, ~TTime, ~`Stim Type`,~Category, ~Condition, ~Correct, ~response_hand, ~response_type)
    data$word_gender <- ifelse((data$Category=="male" & data$Condition=="congruent"),"male","female")
    data$word_gender <- ifelse((data$Category=="female" & data$Condition == "incongruent"),"male",data$word_gender)
    colnames(data) <- c("subject","onset","duration","stim_type","img_gender","trial_type","correct","response_hand","response_type","word_gender")
    # adjust onset to onset of scanner
    data$onset <- data$onset - t_scan
    data$onset <- data$onset/10000
    data$response_time <- data$duration / 10000
    #data$duration <- data$duration/10000
    data$duration = 0.5
    data$response_hand[data$response_type == 'miss'] = NA
    data$response_time[data$response_type == 'miss'] = NA
    
    #data$
    data_format <- data.frame(data$onset,data$duration,data$trial_type,data$img_gender,data$word_gender,data$response_time,data$response_hand,data$response_type)
    colnames(data_format) <- c("onset","duration","trial_type","img_gender","word_gender","response_time","response_hand","response_type")
    fname <- paste0("../logs/gstroop/clean/sub-0",n[i],"_task-gstroop_events.tsv")
    write.table(data_format, file=fname, quote=FALSE, sep='\t', col.names = T, row.names = F)
    #create one long file
    all <- rbind(all,data)
  } 
}
