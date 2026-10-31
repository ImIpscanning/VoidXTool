import requests
from requests import RequestException, Timeout
from rich.console import Console
from loguru import logger
from ezjsonpy import get_config_value, set_config_value, remove_config_value, config_value_exists
from voidxtool.constants import VoidXToolConstants
from voidxtool.utilities.input import Input
from voidxtool.gui.language import Msg

console: Console = Console()

class WebhookUtils:
    COMMAND_NAME: str = 'webhook'

    @staticmethod
    def add_webhook():
        """
        Method to add a webhook.
        """
        webhook_name = Input.get_input(
            Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.webhookName"),
            input_type="string"
        )
        if not webhook_name:
            return None

        webhook_url = Input.get_input(
            Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.webhookUrl"),
            input_type="string"
        )
        if not webhook_url:
            return None

        if not WebhookUtils.discord_webhook_validation(webhook_url):
            console.print(
                Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.invalidWebhookUrl")
            )
            return None

        webhooks = get_config_value("webhooks")
        if webhooks and webhooks != "webhooks":
            for webhook in webhooks:
                if webhooks[webhook] == webhook_url:
                    console.print(
                        Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.webhookUrlAlreadyExists")
                        .replace("%webhookUrl%", f"{webhook_url[:25]}...")
                        .replace("%webhook%", webhook)
                    )
                    return None

        set_config_value(f"webhooks.{webhook_name}", webhook_url)
        console.print(
            Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.webhookAdded")
            .replace("%webhook%", webhook_name)
        )
        return None

    @staticmethod
    def remove_webhook():
        """
        Method to remove a webhook.
        """
        webhook_name = Input.get_input(
            Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.webhookName"),
            input_type="string"
        )
        if not webhook_name:
            return None

        if not config_value_exists(f"webhooks.{webhook_name}"):
            console.print(
                Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.webhookNotFound")
                .replace("%webhook%", webhook_name)
            )
            return None

        remove_config_value(f"webhooks.{webhook_name}")
        console.print(
            Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.webhookRemoved")
            .replace("%webhook%", webhook_name)
        )
        return None

    @staticmethod
    def list_webhooks():
        """
        Method to list all webhooks.

        :return: True if webhook list has content, False otherwise
        """
        webhooks = get_config_value("webhooks")
        if not webhooks or webhooks == "webhooks":
            console.print(
                Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.noWebhooks")
            )
            return False

        if len(webhooks) == 0:
            console.print(
                Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.noWebhooks")
            )
            return False

        console.print(
            Msg.get(f"commands.{WebhookUtils.COMMAND_NAME}.messages.webhookList")
        )
        for webhook in webhooks:
            console.print(
                f"\n{VoidXToolConstants.SPACES}[bold cyan]•[/bold cyan] [bold]{webhook}[/bold]: {webhooks[webhook][:60]}...",
                no_wrap=True
            )
        return True

    @staticmethod
    def discord_webhook_validation(webhook_url: str) -> bool:
        """
        Method to validate a Discord webhook.

        :param webhook_url: The webhook URL
        :return: True if the webhook is valid, False otherwise
        """
        try:
            response = requests.get(webhook_url, timeout=5)
            if response.status_code != 200:
                return False
            return True
        except Timeout:
            logger.warning(f"Timeout error validating webhook: {webhook_url}")
            return False
        except ConnectionError:
            logger.warning(f"Connection error validating webhook: {webhook_url}")
            return False
        except RequestException as e:
            logger.warning(f"Request exception occurred while validating webhook: {webhook_url}, Error: {str(e)}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error validating webhook: {webhook_url}, Error: {str(e)}")
            return False

    @staticmethod
    def send_webhook_message(webhook_url: str, message: str) -> bool:
        """
        Method to send a message to a Discord webhook.

        :param webhook_url: The webhook URL
        :param message: The message to send
        :return: True if the message was sent, False otherwise
        """
        try:
            response = requests.post(webhook_url, json={"content": message}, timeout=5)
            if response.status_code != 204:
                return False
            return True
        except Timeout:
            logger.warning(f"Timeout error sending message to webhook: {webhook_url}")
            return False
        except ConnectionError:
            logger.warning(f"Connection error sending message to webhook: {webhook_url}")
            return False
        except RequestException as e:
            logger.warning(f"Request exception occurred while sending message to webhook: {webhook_url}, Error: {str(e)}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error sending message to webhook: {webhook_url}, Error: {str(e)}")
            return False
