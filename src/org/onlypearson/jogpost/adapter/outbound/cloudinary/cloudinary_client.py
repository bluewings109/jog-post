import json
from io import BytesIO

import cloudinary
import cloudinary.api
import cloudinary.uploader
from PIL.ImageFile import ImageFile
from cloudinary import CloudinaryImage


class CloudinaryClient:
    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
    ):
        # Set configuration parameter: return "https" URLs by setting secure=True
        self.config = cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )

        # Log the configuration
        print("****1. Set up and configure the SDK:****\nCredentials: ", self.config.cloud_name, self.config.api_key, "\n")

    def upload_image(self, file: ImageFile) -> str:

        # Upload the image.
        # Set the asset's public ID and allow overwriting the asset with new versions
        buffer = BytesIO()
        file.save(buffer, format="PNG")
        buffer.seek(0)

        filename = file.filename
        result = cloudinary.uploader.upload(buffer, public_id=filename, unique_filename=False, overwrite=True)

        # Build the URL for the image and save it in the variable 'srcURL'
        src_url = CloudinaryImage(filename).build_url()

        # Log the image URL to the console.
        # Copy this URL in a browser tab to generate the image on the fly.
        print("****2. Upload an image****\nDelivery URL: ", src_url, "\n")
        return src_url

    def get_asset_info(self, filename: str):

        # Get image details and save it in the variable 'image_info'.
        image_info = cloudinary.api.resource(filename)
        print("****3. Get and use details of the image****\nUpload response:\n", json.dumps(image_info, indent=2),"\n")

        # Assign tags to the uploaded image based on its width. Save the response to the update in the variable 'update_resp'.
        if image_info["width"] > 900:
            update_resp = cloudinary.api.update(filename, tags="large")

        elif image_info["width"] > 500:
            update_resp = cloudinary.api.update(filename, tags="medium")

        else:
            update_resp = cloudinary.api.update(filename, tags="small")

        # Log the new tag to the console.
        print("New tag: ", update_resp["tags"], "\n")

    def create_transformation(self, filename: str, width: int, height: int) -> str:

      # Transform the image
      # ==============================

      transformed_url = CloudinaryImage(filename).build_url(width = width, height = height, crop = "fill")

      # Log the URL to the console
      print("****4. Transform the image****\nTransfrmation URL: ", transformed_url, "\n")

      # Use this code instead if you want to create a complete HTML image element:
      # imageTag = cloudinary.CloudinaryImage("quickstart_butterfly").image(radius="max", effect="sepia")
      # print("****4. Transform the image****\nTransfrmation URL: ", imageTag, "\n")

      return transformed_url
