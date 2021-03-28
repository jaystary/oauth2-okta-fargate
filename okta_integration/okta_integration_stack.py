from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets,
    aws_elasticloadbalancingv2 as elb,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_certificatemanager as certmgr,
    aws_route53 as route53,
    aws_certificatemanager as acm,
    core
)


class OktaIntegrationStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        domain_name = "jaysbox.io"
        # Create VPC and Fargate Cluster
        # NOTE: Limit AZs to avoid reaching resource quotas
        vpc = ec2.Vpc(
            self, "OktaVpc",
            max_azs=2
        )

        cluster = ecs.Cluster(
            self, 'OktaCluster',
            vpc=vpc
        )
    
        task_role = iam.Role(self, "OktaRole",
          assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com')
        )

        task_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["lambda:*", "cloudwatch:*", "logs:*"],
            resources=["*"]
        ))
        
        application_hosted_zone = route53.HostedZone.from_lookup(
            self, 'OktaHostedZone',
            domain_name=domain_name
        )

        application_certificate = acm.DnsValidatedCertificate(
            self, 'OktaAlbCertificate',
            hosted_zone=application_hosted_zone,
            domain_name='login.' + domain_name
        )

        image = ecs.ContainerImage.from_asset('../okta_integration/okta-hosted-login')

        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "OktaEcs",
            cluster=cluster,           
            cpu=256,                    
            desired_count=1,            
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=image, 
                container_port=8080,
                task_role=task_role
                ),
            memory_limit_mib=512,
            protocol=elb.ApplicationProtocol.HTTPS,
            certificate=application_certificate,
            domain_name='login.' + domain_name,
            domain_zone=application_hosted_zone,
            public_load_balancer=True)

        fargate_service.target_group.configure_health_check(
            port='8080',
            path='/health',
            timeout=core.Duration.seconds(20),
            healthy_threshold_count=2,
            unhealthy_threshold_count=10,
            interval=core.Duration.seconds(30),
        )

        fargate_service.listener.add_certificates(
            'ApplicationServiceCertificate',
            certificates=[ application_certificate ]
        )

        fargate_service.load_balancer.connections.allow_to_any_ipv4(
            port_range= ec2.Port(
                from_port=443,
                to_port=443,
                protocol=ec2.Protocol.TCP,
                string_representation='Allow ALB to verify token'
            )
        )

        core.CfnOutput(
            self, "LoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name
        )
