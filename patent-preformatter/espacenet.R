# The script transforms Espacenet search result into common format (XLSX)

library("readxl")
library("writexl")

# --- Utility functions ---

# Concatenates elements of vector into one element; semicolon is separator.
ConcatSemicolon <- function(vals) {
  return(paste(vals, collapse = "; "))
}

# Concatenates elements of vector into one element; comma is separator.
ConcatComma <- function(vals) {
  return(paste(vals, collapse = ", "))
}

# Returns index of '[' char at string if it appears, or string length otherwise
GetBracketIdx <- function(str) {
  return(ifelse(grepl("\\[", str), regexpr("\\[", str) - 2, nchar(str)))
}

# Remove country-related postfix from the string
RmCountryPostfix <- function(str) {
  return(substr(str, start = 1, stop = GetBracketIdx(str)))
}

# Extracts country id from patent id at non-formatted data
GetCountry <- function(patent_id) {
  return(substr(patent_id, start = 1, stop = 2))
}

# Extracts type from patent id at non-formatted data
GetPatentType <- function(patent_id) {
  patent_ids <- strsplit(patent_id, " ")
  first_ids <- lapply(patent_ids, "[[", 1)
  no_country_id <- substr(first_ids, start = 3, stop = length(first_ids))
  type_str_id <- regexpr("[AB]", no_country_id)
  type_ids <- lapply(type_str_id, "[[", 1)
  return(substr(no_country_id, start = type_ids, stop = length(no_country_id)))
}

# Extracts number from patent id at non-formatted data
GetPatentNum <- function(patent_id) {
  patent_ids <- strsplit(patent_id, " ")
  ids <- lapply(patent_ids, "[[", 1)
  num_id <- regexpr("[0-9]+", ids)
  num_length <- attr(num_id, "match.length")
  num_str <- substr(ids, start = num_id, stop = num_id + num_length - 1)
  return(as.numeric(num_str))
}

# Extracts classifiers from IPC at non-formatted data
GetClassifiers <- function(ipc) {
  ipcs <- strsplit(ipc, " \r\n")
  classifiers <- lapply(ipcs, ConcatSemicolon)
  return(classifiers)
}

# Extracts applicant name from non-formatted data
GetApplName <- function(appl_str) {
  applicants <- RmCountryPostfix(appl_str)
  return(trimws(applicants))
}

# Extracts applicant's country from non-formatted data
GetApplCountry <- function(appl_str) {
  country_idx <- regexpr("\\[", appl_str)
  return(ifelse(
    country_idx == -1,
    "",
    substr(appl_str, start = country_idx + 1, stop = country_idx + 2)
  ))
}

# Extracts inventors from non-formatted data
GetInventors <- function(inventor_str) {
  split <- strsplit(inventor_str, " \r\n")
  no_country_inventors <- lapply(split, RmCountryPostfix)
  inventors <- lapply(no_country_inventors, ConcatComma)
  return(inventors)
}

# Extracts year from the date; it should be YYYY-MM-DD formatted
GetYear <- function(date) {
  reduced <- substr(date, start = 1, stop = 10)
  year <- substr(reduced, start = 1, stop = 4)
  return(as.numeric(year))
}

# --- Main part of the script ---

args = commandArgs(trailingOnly=TRUE)

# test if there is at least one argument: if not, return an error
if (length(args) == 0) {
  stop("At least one argument must be supplied (input file).n", call.=FALSE)
}

input_file <- args[1]

sprintf("Start transforming '%s'...", input_file)

if (!file_test("-f", input_file)) {
  sprintf("Can't find input file '%s', exit.", input_file)
  q()
}

# Espacenet data frame columns names
in_num <- "No"
in_title <- "Title"
in_inventor <- "Inventors"
in_appl_name <- "Applicants"
in_publ_num <- "Publication number"
in_priority <- "Earliest priority"
in_ipc <- "IPC"
in_cpc <- "CPC"
in_publ_date <- "Publication date"
in_earl_publ <- "Earliest publication"
in_family <- "Family number"

# Get input data
input_dframe <- readxl::read_excel(input_file, "Results")

in_publ_nums <- input_dframe[, in_publ_num]
in_ipcs <- input_dframe[, in_ipc]
in_appl_names <- input_dframe[, in_appl_name]
in_inventors <- input_dframe[, in_inventor]
in_priorities <- input_dframe[, in_priority]
in_publ_dates <- input_dframe[, in_earl_publ]
in_titles <- input_dframe[, in_title]

# Common format data frame columns names
out_country <- "Страна выдачи"
out_patent_type <- "Вид патента"
out_patent_num <- "Номер патента"
out_patent_id <- "Full ID"
out_url <- "Link"
out_ipc <- "Классификационный индекс"
out_classifiers <- "Классификатор(ы)"
out_search_subj <- "Предмет поиска"
out_appl_name <- "Заявитель"
out_appl_country <- "Страна заявитель"
out_inventor <- "Изобретатель"
out_appl_num <- "Номер заявки"
out_prior_date <- "Дата приоритета"
out_prior_docs <- "Приоритетные документы"
out_appl_date <- "Дата подачи заявки"
out_appl_year <- "Год подачи заявки"
out_publ_date <- "Дата публикации"
out_publ_year <- "Год публикации"
out_title <- "Название"
out_status <- "Сведения о действии"

out_col_names <- c(
  out_country, out_patent_type, out_patent_num, out_patent_id, out_url, out_ipc,
  out_classifiers, out_search_subj, out_appl_name, out_appl_country,
  out_inventor, out_appl_num, out_prior_date, out_prior_docs, out_appl_date,
  out_appl_year, out_publ_date, out_publ_year, out_title, out_status
)
out_matrix <- matrix(ncol = length(out_col_names), nrow = nrow(input_dframe))
out_dframe <- data.frame(out_matrix)

# Calculate formatted values for output dataframe
countries <- sapply(in_publ_nums, GetCountry)
patent_types <- sapply(in_publ_nums, GetPatentType)
patent_nums <- sapply(in_publ_nums, GetPatentNum)
patent_ids <- paste(countries, patent_nums, patent_types, sep = "-")
classifiers <- unlist(sapply(in_ipcs, GetClassifiers))
applicants <- sapply(in_appl_names, GetApplName)
appl_countries <- sapply(in_appl_names, GetApplCountry)
publ_years <- sapply(in_publ_dates, GetYear)
inventors <- unlist(sapply(in_inventors, GetInventors))

# Store values to output dataframe
colnames(out_dframe) <- out_col_names
out_dframe[, out_country] <- countries
out_dframe[, out_patent_type] <- patent_types
out_dframe[, out_patent_num] <- patent_nums
out_dframe[, out_patent_id] <- patent_ids
out_dframe[, out_ipc] <- classifiers
out_dframe[, out_appl_name] <- applicants
out_dframe[, out_appl_country] <- appl_countries
out_dframe[, out_inventor] <- inventors
out_dframe[, out_prior_date] <- in_priorities
out_dframe[, out_publ_date] <- in_publ_dates
out_dframe[, out_publ_year] <- publ_years
out_dframe[, out_title] <- in_titles

# Clean previous result, if exists
out_file <- "espacenet-patents.xlsx"
if (file_test("-f", out_file)) {
  file.remove(out_file)
  print("Clearing previous results...done!")
}

# Save the formatted result
sprintf("Writing the result to '%s'", out_file)
writexl::write_xlsx(out_dframe, out_file)

print("Transforming is complete.")
