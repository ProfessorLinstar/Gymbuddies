function showFieldError(element, str, elementError, pattern) {
  if (element.validity.valueMissing) {
    elementError.textContent = "You need to enter a " + str;
  } else if (element.validity.typeMismatch) {
    elementError.textContent = "Entered value needs to be a " + str;
  } else if (element.validity.tooShort) {
    elementError.textContent = str + ' should be at least ' + element.minLength + ' characters; you entered ' + element.value.length;
  } else if (element.validity.patternMismatch) {
    console.log("validity:", element.validity);
    if (element.pattern === "(^\\S.*\\S$|^\\S$)") {
      elementError.textContent = "Entered value cannot have leading/trailing whitespace."
    } else {
      elementError.textContent = "Entered value needs to have " + pattern;
    }
  }
  else if (element.validity.tooLong) {
    // If the data is too short,
    // display the following error message.
    elementError.textContent = str + ' should be at most ' + element.maxLength + ' characters; you entered ' + element.value.length;
  }

  // Set the styling appropriately
  elementError.className = "invalid-feedback";
  elementError.style.display = "block";
  element.className = "form-control is-invalid focus"
}

function validateGenderPref() {
  okbin = document.getElementById('okbinary');
  okmale = document.getElementById('okmale');
  okfemale = document.getElementById('okfemale');
  return okbin.checked || okmale.checked || okfemale.checked;
}

function showGenderPrefError(elementError) {
  if (!validateGenderPref()) {
    elementError.textContent = "Select at least one option";
  }

  // Set the styling appropriately
  elementError.className = "invalid-feedback";
  elementError.style.display = "block";
  // element.className = "form-control is-invalid focus"
}

function getFields() {
  const name = document.getElementById("name");
  const contact = document.getElementById("contact");
  const bio = document.getElementById("bio");
  const nameError = document.querySelector("#name + span.invalid-feedback");
  const contactError = document.querySelector("#contact + span.invalid-feedback");
  const bioError = document.querySelector("#bio + span.invalid-feedback");
  const genderpError = document.querySelector("#genderPrefFeedback");
  return [name, contact, bio, nameError, contactError, bioError, genderpError];
}

function validate() {
  const [name, contact, bio, nameError, contactError, bioError, genderpError] = getFields();
  let error = 0
  if (!name.validity.valid) {
    showFieldError(name, "name", nameError);
    error = 1;
  }
  if (!contact.validity.valid) {
    showFieldError(contact, "phone number", contactError, "10 digits, no special characters");
    error = 1;
  }
  if (!bio.validity.valid) {
    showFieldError(bio, "bio", bioError);
    error = 1;
  } if (!validateGenderPref()) {
    showGenderPrefError(genderpError);
    error = 1;
  }
  return error;
}

function bindEvents() {
  const [name, contact, bio, nameError, contactError, bioError, genderpError] = getFields();

  console.log("name:", name);
  console.log("contact:", contact);
  console.log("bio:", bio);
  console.log("nameError:", nameError);
  console.log("contactError:", contactError);
  console.log("bioError:", bioError);
  console.log("genderpError:", genderpError);


  name.addEventListener("focusout", (event) => {
    // Each time the user types something, we check if the
    // form fields are valid.

    console.log("inside name addeventlistener")
    if (name.validity.valid) {
      // In case there is an error message visible, if the field
      // is valid, we remove the error message.
      nameError.textContent = ""; // Reset the content of the message
      nameError.className = "invalid-feedback"; // Reset the visual state of the message
      name.className = "form-control is-valid"

    } else {
      // If there is still an error, show the correct error
      showFieldError(name, "name", nameError);
    }
  });

  contact.addEventListener("focusout", (event) => {
    // Each time the user types something, we check if the
    // form fields are valid.

    console.log("inside contact addeventlistener")
    if (contact.validity.valid) {
      // In case there is an error message visible, if the field
      // is valid, we remove the error message.
      contactError.textContent = ""; // Reset the content of the message
      contactError.className = "invalid-feedback"; // Reset the visual state of the message
      contact.className = "form-control is-valid"

    } else {
      // If there is still an error, show the correct error
      showFieldError(contact, "phone number", contactError, "10 digits, no special characters");
    }
  });

  bio.addEventListener("focusout", (event) => {
    // Each time the user types something, we check if the
    // form fields are valid.

    console.log("inside bio addeventlistener")
    if (bio.validity.valid) {
      // In case there is an error message visible, if the field
      // is valid, we remove the error message.
      bioError.textContent = ""; // Reset the content of the message
      bioError.className = "invalid-feedback"; // Reset the visual state of the message
      bio.className = "form-control is-valid"

    } else {
      // If there is still an error, show the correct error
      showFieldError(bio, "bio", bioError);
    }
  });

}

// form.addEventListener("submit", (event) => {
//   // if the email field is valid, we let the form submit
//   if (!contact.validity.valid) {
//     // If it isn't, we display an appropriate error message
//     showFieldError();
//     // Then we prevent the form from being sent by canceling the event
//     event.preventDefault();
//   }
// });
